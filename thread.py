import json
import re
from datetime import datetime

from utils.aws import read_file_from_s3, write_file_to_s3, file_exists_in_s3


class Thread:
    colors = {
        "system": "\033[1;37m",
        "user": "\033[1;31m",
        "assistant": "\033[1;34m",
        "tool": "\033[1;32m"
    }

    def __init__(self, client, bucket, thread_id, tools=None, messages=None, tool_calls=None, is_active=True, model="gpt-4o", **kwargs):
        self.client = client
        self.bucket = bucket
        self.thread_id = thread_id
        self.tools = tools
        self.tool_calls = {}
        self.is_active = is_active
        self.model = model

        if messages is not None:
            self.messages = messages
            for message in messages:
                tool_calls = message.get('tool_calls')
                if tool_calls is not None:
                    for tool_call in tool_calls:
                        self.tool_calls[tool_call['id']] = tool_call
        else:
            self.messages = []
    

    def add_message(self, message, print_message=True):
        message['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.messages.append(message)

        if message['content'] is not None and print_message:
            if message['role'] == 'tool':
                self._print_tool(message)
            else:
                self._print_message(message)
            print()

        tool_calls = message.get('tool_calls')
        if tool_calls is not None:
            for tool_call in tool_calls:
                self.tool_calls[tool_call['id']] = tool_call
        
    
    def _get_nameplate(self, message):
        color = Thread.colors[message['role']]
        name = message['role'].upper()

        return f"{color}{name}\033[0m:"


    def _print_message(self, message):
        nameplate = self._get_nameplate(message)
        print(f"{nameplate} {message['content']}")

    
    def _print_tool(self, message):
        nameplate = self._get_nameplate(message)
        tool_call = self.tool_calls[message['tool_call_id']]
        print(f"{nameplate} {tool_call['function']['name']}\n Inputs: {tool_call['function']['arguments']}\n Output: {message['content']}")
    

    def get_tool_call(self, message):
        tool_call = self.tool_calls[message['tool_call_id']]
        return tool_call['function']


    def _print_conversation(self):
        for message in self.messages:
            if message['content'] is not None:
                if message['role'] == 'tool':
                    self._print_tool(message)
                else:
                    self._print_message(message)
                print()
    

    def get_response(self, extra_messages=[]):
        if self.tools is None:
            return self.client.chat.completions.create(
                model = self.model,
                messages = self.messages+extra_messages
            ).choices[0]
        else:
            return self.client.chat.completions.create(
                model = self.model,
                messages = self.messages+extra_messages,
                tools = [tool.description for tool in self.tools.values()],
                tool_choice = "auto"
            ).choices[0]


    def run(self):
        if not self.is_active:
            return None
        
        completion = self.get_response()
                
        while completion.finish_reason != "stop":
            self.add_message(completion.message.to_dict())
            
            for tool_call in completion.message.tool_calls:
                args = eval(tool_call.function.arguments)

                try:
                    result = self.tools[tool_call.function.name].run(instance=self, **args)
                except KeyError:
                    raise ValueError(f"Tool {tool_call.function.name} not found")
                
                self.add_message({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "content": str(result)
                })
            
            completion = self.get_response()

        template_pattern = r'\[.*?\]'
        placeholder_present = re.search(template_pattern, completion.message.content)
        while placeholder_present:
            completion = self.get_response(extra_messages=[completion.message.to_dict(), {"role": "system", "content": f"REJECTED: Placeholder detected in response: {placeholder_present}. Rewrite your message without any placeholders, but do not invent any information."}])
            placeholder_present = re.search(template_pattern, completion.message.content)

        self.add_message(completion.message.to_dict())

        return completion.message.content


    def to_json(self):
        return json.dumps({
            "messages": self.messages,
            "thread_id": self.thread_id,
            "is_active": self.is_active,
        })
    

    @classmethod
    def from_json(cls, client, bucket, json_str, tools=None):
        data = json.loads(json_str)
        return cls(client, bucket, tools=tools, **data)
    

    def save(self):
        key = f"threads/{self.thread_id}.json"
        write_file_to_s3(self.bucket, key, self.to_json())


    @classmethod
    def load(cls, client, bucket, thread_id, tools=None):
        key = f"threads/{thread_id}.json"
        json_str = read_file_from_s3(bucket, key)
        return cls.from_json(client, bucket, json_str, tools=tools)


    @classmethod
    def exists(cls, bucket, thread_id):
        key = f"threads/{thread_id}.json"
        return file_exists_in_s3(bucket, key)


    def deactivate(self):
        self.is_active = False
        self.save()
    

    def activate(self):
        self.is_active = True
        self.save()
