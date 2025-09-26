# class CLI:

#     SHELL_PROMPT = "$> "

#     def start_shell(self):
#         """Start the command-line interface shell."""
#         command = ""
#         while command != "exit":
#             command = input(self.SHELL_PROMPT).strip()
#             if command == "help":
#                 print("Available commands:")
#                 for cmd in list_commands():
#                     print(f" - {cmd}")
#             elif command == "exit":
#                 print("Exiting CLI.")
#             else:
#                 try:
#                     result = call_command(command)
#                     print(f"Command '{command}' executed successfully. Result: {result}")
#                 except KeyError as e:
#                     print(e)
