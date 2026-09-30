r"""
The StressTest reproduction (reproduce_stresstest_gemma.py) for Qwen2-Audio-7B-Instruct
and the paper's own fix, StresSLM (a LoRA adapter on it, slprl/StresSLM).

Qwen2-Audio is the model the paper fine-tuned: 0.532 SSR / 0.331 SSD before,
0.862 / 0.869 after (StresSLM). Running both reproduces the paper's headline
before/after on our machine, with the same prompts, parsing and scoring as every
other model here (only the generation call is swapped, as in
reproduce_stresstest_server.py).

Generation copies the authors' client
(stresstest/evaluation/src/inference/inference_client_qwen2_audio.py): the chat
template with the audio before the prompt, audio resampled to the processor's
rate, the model's bundled sampling defaults (do_sample, T 0.7, top_p 0.5, top_k
20, repetition penalty 1.1), up to 512 tokens; seeded per sample here. Two
deviations, both about fitting a 16 GB card: bf16 weights (they loaded the
default dtype) and accelerate spilling what doesn't fit to CPU RAM (same
weights, slower). Thinking conditions don't apply; run --conditions nothink.

    python reproduce_stresstest_qwen2audio.py --model Qwen/Qwen2-Audio-7B-Instruct --conditions nothink --tasks ssr,ssd
    python reproduce_stresstest_qwen2audio.py --model slprl/StresSLM --conditions nothink --tasks ssr,ssd
    ... --dataset stresspresso
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reproduce_stresstest_gemma as R  # noqa: E402

BASE = "Qwen/Qwen2-Audio-7B-Instruct"
_MODEL = None
_PROCESSOR = None


def _load():
    global _MODEL, _PROCESSOR
    if _MODEL is None:
        import torch
        from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration
        _PROCESSOR = AutoProcessor.from_pretrained(BASE)
        free = torch.cuda.mem_get_info()[0] / 2**30
        _MODEL = Qwen2AudioForConditionalGeneration.from_pretrained(
            BASE, dtype=torch.bfloat16, device_map="auto",
            max_memory={0: f"{max(4, int(free) - 3)}GiB", "cpu": "64GiB"})
        if R.MODEL_ID != BASE:  # an adapter on top, e.g. slprl/StresSLM
            from peft import PeftModel
            _MODEL = PeftModel.from_pretrained(_MODEL, R.MODEL_ID)
        _MODEL.eval()
    return _MODEL, _PROCESSOR


def qwen_generate(prompt: str, wav: Path | None, thinking: bool, seed: int,
                  max_new_tokens: int = 512) -> dict:
    """Drop-in for R.gemma(); `thinking` is ignored (Qwen2-Audio has no such mode)."""
    import librosa
    import torch
    from transformers import set_seed
    model, processor = _load()
    content = [{"type": "text", "text": prompt}]
    audio = None
    if wav is not None:
        content.insert(0, {"type": "audio", "audio_url": str(wav)})
        audio = [librosa.load(str(wav), sr=processor.feature_extractor.sampling_rate)[0]]
    text = processor.apply_chat_template([{"role": "user", "content": content}],
                                         add_generation_prompt=True, tokenize=False)
    inputs = processor(text=[text], audio=audio, return_tensors="pt", padding=True,
                       sampling_rate=processor.feature_extractor.sampling_rate)
    inputs = {k: v.to("cuda") if torch.is_tensor(v) else v for k, v in inputs.items()}
    n_in = inputs["input_ids"].shape[-1]
    set_seed(seed)
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens)
    elapsed = time.perf_counter() - t0
    n_tok = out.shape[-1] - n_in
    reply = processor.batch_decode(out[:, n_in:], skip_special_tokens=True,
                                   clean_up_tokenization_spaces=False)[0]
    return {"content": reply.strip(), "thinking": "", "n_tokens": int(n_tok),
            "hit_token_limit": n_tok >= max_new_tokens - 8, "elapsed_s": round(elapsed, 2)}


if __name__ == "__main__":
    R.gemma = qwen_generate  # run_one() and the rule-failure judge both call R.gemma
    sys.exit(R.main())
