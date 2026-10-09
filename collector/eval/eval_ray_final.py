"""Legacy evaluation entry point; caller must now supply --cases or --result.

Historical Ray results remain in ray-prompt-eval; this entry never overwrites them.
"""
from eval_account_general import main

if __name__ == '__main__':
    raise SystemExit(main())
