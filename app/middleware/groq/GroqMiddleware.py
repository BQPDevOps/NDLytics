import os
from config import config

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class GroqMiddleware:
    def __init__(self, model, temperature, max_tokens):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._load_env_config()

    def _load_env_config(self):
        os.environ["langchain_api_key"] = config.api_key_langchain
        os.environ["GROQ_API_KEY"] = config.api_key_groq

    def _define_prompt(self, prompt_template):
        """
        Creates a ChatPromptTemplate with the given template.
        The template should use {variable_name} for variables.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_template),
            ]
        )
        return prompt

    def generate_response(self, prompt: str, variables: dict) -> str:
        """
        Generate a response using the Groq API.

        Args:
            prompt: The prompt template string with {variable_name} placeholders
            variables: Dictionary of variables to fill in the template

        Returns:
            str: The generated response
        """
        prompt_template = self._define_prompt(prompt)

        llm = ChatGroq(
            model=self.model, temperature=self.temperature, max_tokens=self.max_tokens
        )

        output_parser = StrOutputParser()
        chain = prompt_template | llm | output_parser

        try:
            response = chain.invoke(variables)
            return response
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Error generating insights. Please try again later."
