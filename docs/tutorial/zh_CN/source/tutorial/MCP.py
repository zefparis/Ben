# -*- coding: utf-8 -*-
"""
.. _MCP:

MCP
====================

在本教程中，我们将简要介绍什么是 MCP，并展示如何在 AgentScope 中使用 MCP。此外，我们将演示如何将现有的 AgentScope 多智能体应用配置为 MCP 服务器。最后，为了帮助高级开发者更深入地理解，我们将讨论 MCP 是如何与 AgentScope 集成的。

.. note:: 1.阅读本章节之前，请先阅读《工具》章节，以了解最基本的`ServiceToolkit`模块的基本使用方法。

 2. 在AgentScope中使用MCP，要求你的 Python 版本不低于 3.10，并至少安装 `agentscope[service]` 版本。
"""

# %%
# 什么是MCP
# --------------------------
# MCP（Model Context Protocol，模型上下文协议）是由 Anthropic 推出的一种开放标准，旨在规范大型语言模型与外部数据源和工具之间的通信方式，使 AI 模型能够充分发挥潜力。
# 通过 MCP，AI 应用可以安全地访问和操作本地及远程数据，为 AI 应用提供了一种类似于“USB-C 接口”的连接方式。
# 这一标准不仅促进了服务商开发 API 的便利性，也避免了开发者重复构建基础功能，使现有的 MCP 服务能够增强智能代理的能力。例如，MCP 服务器可以提供预定义的提示模板，用于生成电子邮件草稿或优化代码注释，从而提升应用开发效率和质量。

# %%
# MCP支持两种通信协议：标准输入输出（STDIO）和 HTTP的Server-Sent Events（SSE）。
# - STDIO 协议用于本地通信，涉及通过标准输入和输出进行消息传输（即，MCP Server也启动在本地）。这种方式的实现通常涉及逐行解析和处理消息，适用于在同一计算环境中运行的客户端和服务器之间的通信。
# - HTTP 协议则用于远程通信（即，MCP Server启动在远端），通过将 JSON-RPC 消息封装为 SSE 事件来实现。这种机制允许服务器通过持续开放的 HTTP 连接将事件推送到客户端。

# %%
# 把MCP服务器添加到`ServiceToolkit`
# --------------------------
# AgentScope作为MCP客户端，支持一键启动本地的 MCP 服务器并建立基于 STDIO 协议的连接，也支持使用 SSE 协议与远程的 MCP 服务器建立会话。这些使用方式均基于`ServiceToolkit.add_mcp_servers`的接口。以下代码展示了如何通过 STDIO 在本地启动并连接一个提供浏览器自动化功能的服务器。该服务器使用 Puppeteer，使得大模型能够与网页互动、截取屏幕截图以及在真实的浏览器环境中执行 JavaScript。请注意，在使用以下 MCP 服务器之前，请确保在您的系统中安装了 `Node.js` 以确保 `npx` 命令可以正常运行。


from agentscope.service import ServiceToolkit

local_configs = {
    "mcpServers": {
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        },
    },
}

# %%
# 初始化 ServiceToolkit 并添加 MCP 服务器配置 （在自己的环境中取消注释下面的代码）
# 注意：如果您需要使用 STDIO MCP Server，请确保对象不会跨线程使用。
# 因为在一个线程中，标准输入/输出流可能会被回收，
# 导致潜在的冲突或意外行为。

toolkit = ServiceToolkit()
# toolkit.add_mcp_servers(server_configs=local_configs)

# %%
# 输出工具配置的指令以验证设置
print(toolkit.tools_instruction)

# %%
# 如果你需要使用HTTP协议连接在远程的服务器（或者是在本地其他进程启动SSE协议的MCP服务器），你可以参考以下配置进行连接。

remote_configs = {
    "mcpServers": {
        "puppeteer": {
            "url": "http://127.0.0.1:8000/sse",
        },
    },
}

# %%
# 把多智能体应用添加到MCP服务器
# --------------------------
# 你可以通过MCP官方提供的Python SDK轻松地将多智能体应用添加到自己的MCP服务器。以下是一个示例代码，演示如何使用AgentScope和MCP库来实现这一目的。

import agentscope

from agentscope.agents import DialogAgent
from agentscope.message import Msg
from mcp.server import FastMCP
from pydantic import Field

agentscope.init(
    model_configs={
        "config_name": "my-qwen-max",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
    },
)

mcp = FastMCP("My MCP Server")


# %%
# 使用@mcp.tool()装饰器定义工具，这里我们使用AgentScope的 `DialogAgent` 创建一个讲笑话的工具。


@mcp.tool()
def tell_a_joke(
    topic: str = Field(
        description="The topic of a joke",
    ),
) -> str:
    """Generate a joke based on the given topic"""
    agent = DialogAgent(
        name="FunnyBot",
        model_config_name="my-qwen-max",
        sys_prompt="You are a witty comedian tasked with creating a joke about the given topic.",
    )
    msg_task = Msg("user", topic, "user")
    res = agent(msg_task)

    return res.content


# %%
# 将上面的代码保存到文件 `my_mcp_server.py` 中。
# 然后，在终端中运行以下命令来启动服务器：
# `mcp run my_mcp_server.py -t sse`
# 此命令会启动 MCP 服务器，并将工具调用结果以服务器推送事件（SSE）的方式进行传输。
# 这样，就可以通过配置的 MCP 服务器来访问和使用这一多智能体应用。

# 如果您在子进程中运行上述代码（例如，作为 STDIO 服务器启动），
# 请在顶部添加以下语句，以确保服务器在子进程结束后可以被回收。

import nest_asyncio

nest_asyncio.apply()
