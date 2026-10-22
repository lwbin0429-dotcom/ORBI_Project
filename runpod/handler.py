"""Optional custom worker; the current deployment uses managed RunPod vLLM.

Install runpod/requirements.txt in a GPU-capable image and configure MODEL_NAME
only if deploying this alternative worker. The Flask app never loads weights.
"""

import os
from functools import lru_cache

import runpod


@lru_cache(maxsize=1)
def load_model():
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_name = os.getenv("MODEL_NAME", "").strip()
    if not model_name:
        raise ValueError("Configure MODEL_NAME with the actual deployed model.")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", torch_dtype="auto",
    )
    model.eval()
    return model_name, tokenizer, model


def handler(job: dict) -> dict:
    import torch

    data = job.get("input", {})
    messages = data.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 8:
        raise ValueError("Supply a bounded messages list.")
    for message in messages:
        if (
            not isinstance(message, dict)
            or message.get("role") not in {"system", "user", "assistant"}
            or not isinstance(message.get("content"), str)
            or len(message["content"]) > 64000
        ):
            raise ValueError("Invalid message.")
    model_name, tokenizer, model = load_model()
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    sampling = data.get("sampling_params", {})
    max_tokens = int(sampling.get("max_tokens", 1100))
    temperature = min(max(float(sampling.get("temperature", 0.6)), 0.01), 1.0)
    with torch.inference_mode():
        tokens = model.generate(
            **inputs,
            max_new_tokens=min(max(max_tokens, 1), 1100),
            do_sample=True,
            temperature=temperature,
            pad_token_id=tokenizer.eos_token_id,
        )
    text = tokenizer.decode(
        tokens[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True,
    )
    return {"model": model_name, "text": text}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
