import argparse
import sys

from assistant.ai.client import ask_ai


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="signaltrust-assistant",
        description="SignalTrust Assistant CLI"
    )

    subparsers = parser.add_subparsers(dest="command")

    # --- AI root command ---
    ai_parser = subparsers.add_parser("ai", help="Interact with the AI")
    ai_subparsers = ai_parser.add_subparsers(dest="ai_command")

    # ai ask
    ask_parser = ai_subparsers.add_parser("ask", help="Send a one-shot prompt to the AI")
    ask_parser.add_argument("prompt", type=str, help="Prompt to send to the AI")

    # ai chat
    chat_parser = ai_subparsers.add_parser("chat", help="Chat with the AI")
    chat_parser.add_argument("prompt", type=str, help="Prompt to send to the AI")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ai":
        if args.ai_command == "ask":
            result = ask_ai(args.prompt)
            print(result)
            return 0

        if args.ai_command == "chat":
            result = ask_ai(args.prompt)
            print(result)
            return 0

        parser.print_help()
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
