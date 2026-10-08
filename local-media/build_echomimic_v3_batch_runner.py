"""Build a benchmark-only EchoMimic V3 runner that loads weights once."""

from __future__ import annotations

import sys
from pathlib import Path


def main(source: Path, target: Path) -> None:
    text = source.read_text(encoding="utf-8")
    audio_arg = '    parser.add_argument("--audio_path", type=str, required=True, help="Input audio path")\n'
    text = text.replace(
        audio_arg,
        audio_arg + '    parser.add_argument("--batch_manifest", type=str, required=True, help="Benchmark jobs JSON")\n',
        1,
    )
    text = text.replace(
        "    audio_path = args.audio_path\n",
        "    audio_path = args.audio_path\n    batch_manifest = args.batch_manifest\n",
        1,
    )
    generator_at = text.index("    generator = torch.Generator(device=device).manual_seed(seed)")
    body_at = text.index("    with torch.no_grad():\n", generator_at)
    body_start = body_at + len("    with torch.no_grad():\n")
    body_end = text.index("\nif __name__ == \"__main__\":", body_start)
    body = text[body_start:body_end]
    body = body.replace("            return\n", "            continue\n")
    body = "\n".join(("    " + line if line else line) for line in body.splitlines()) + "\n"
    loop = '''    jobs = json.loads(Path(batch_manifest).read_text(encoding="utf-8"))
    batch_started = time.monotonic()
    with torch.no_grad():
        for batch_index, batch_job in enumerate(jobs):
            image_path = batch_job["image"]
            audio_path = batch_job["audio"]
            save_path = batch_job["save_path"]
            seed = int(batch_job.get("seed", seed))
            generator = torch.Generator(device=device).manual_seed(seed)
            os.makedirs(save_path, exist_ok=True)
            torch.cuda.reset_peak_memory_stats()
            job_started = time.monotonic()
'''
    epilogue = '''            elapsed = time.monotonic() - job_started
            output_path = os.path.join(save_path, f"{image_name}_output.mp4")
            final_path = os.path.join(save_path, "output.mp4")
            if os.path.exists(output_path):
                os.replace(output_path, final_path)
            performance = {
                "model": "echomimic_v3_flash",
                "exit_code": 0,
                "wall_seconds": round(elapsed, 3),
                "batch_startup_seconds": round(job_started - batch_started, 3),
                "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                "peak_gpu_memory_mb": round(torch.cuda.max_memory_reserved() / 1024 / 1024, 1),
                "execution_mode": "warm_batch_after_single_model_load",
            }
            Path(save_path, "performance.json").write_text(
                json.dumps(performance, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"BATCH_RESULT {batch_index + 1}/{len(jobs)} {json.dumps(performance)}", flush=True)
'''
    text = text[:generator_at] + loop + body + epilogue + text[body_end:]
    text = text.replace("import argparse\n", "import argparse\nimport resource\nimport time\nfrom pathlib import Path\n", 1)
    compile(text, str(target), "exec")
    target.write_text(text, encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
