# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: sphinx
#       format_version: '1.1'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

"""
.. _distribution:

Distribution
============

This section introduces the usage of the distributed mode of AgentScope. AgentScope natively provides a distributed mode based on gRPC.
In this mode, multiple agents in one application can be deployed to different processes or even different machines, thereby fully utilizing computational resources and improving efficiency.

Basic Usage
~~~~~~~~~~~

The distributed mode of AgentScope requires no modification to the main
process code compared to the traditional mode. You only need to call the
``to_dist`` function when initializing your agent.

This section will showcase how to use the distributed mode of AgentScope with
a web search case.
To highlight the acceleration effect brought by the distributed mode of
AgentScope, a simple custom ``WebAgent`` is used here.
``WebAgent`` will sleep 5 seconds to simulate the process of crawling a
webpage and looking for answers from it, and there are 5 agents in the example.

The process of performing the search is the ``run`` function. The difference
between the traditional and distributed mode is only in the initialization
stage, namely ``init_without_dist`` and ``init_with_dist``.
In distributed mode, you have to call the ``to_dist`` function, which turns
the original Agent into the corresponding distributed version.

.. code-block:: python

    # Please do not run this code in jupyter notebook.
    # Please copy the code to the ``dist_main.py`` file and use the ``python dist_main.py`` command to run this code.
    # Please install the distributed version of agentscope before running this code.

    import time
    import agentscope
    from agentscope.agents import AgentBase
    from agentscope.message import Msg

    class WebAgent(AgentBase):

        def __init__(self, name):
            super().__init__(name)

        def get_answer(self, url: str, query: str):
            time.sleep(5)
            return f"Answer from {self.name}"

        def reply(self, x: dict = None) -> dict:
            return Msg(
                name=self.name,
                content=self.get_answer(x.content["url"], x.content["query"])
            )


    QUERY = "example query"
    URLS = ["page_1", "page_2", "page_3", "page_4", "page_5"]

    def init_without_dist():
        return [WebAgent(f"W{i}") for i in range(len(URLS))]


    def init_with_dist():
        return [WebAgent(f"W{i}").to_dist() for i in range(len(URLS))]


    def run(agents):
        start = time.time()
        results = []
        for i, url in enumerate(URLS):
            results.append(agents[i].reply(
                Msg(
                    name="system",
                    role="system",
                    content={
                        "url": url,
                        "query": QUERY
                    }
                )
            ))
        for result in results:
            print(result.content)
        end = time.time()
        return end - start


    if __name__ == "__main__":
        agentscope.init()
        start = time.time()
        simple_agents = init_without_dist()
        dist_agents = init_with_dist()
        end = time.time()
        print(f"Initialization time: {end - start}")
        print(f"Runtime without distributed mode: {run(simple_agents)}")
        print(f"Runtime with distributed mode: {run(dist_agents)}")


The output of running this sample is as follows:

.. code-block:: text

    Initialization time: 16.50428819656372
    Answer from W0
    Answer from W1
    Answer from W2
    Answer from W3
    Answer from W4
    Runtime without distributed mode: 25.034368991851807
    Answer from W0
    Answer from W1
    Answer from W3
    Answer from W2
    Answer from W4
    Runtime with distributed mode: 5.0517587661743164

From the sample output above, we can observe that the running speed has
significantly improved after adopting the distributed mode (25 s -> 5 s).

The example above is the most common use case for the distributed mode of
AgentScope. It is recommended to use this method directly when not aiming
for extreme performance. If you require further performance optimization,
a deeper understanding of the distributed mode of AgentScope is necessary.
The advanced usage method of AgentScope distributed mode will be introduced
in the following sections.
"""

###############################################################################
# Advanced Usage
# ~~~~~~~~~~~~~~~
#
# This section will introduce advanced usage methods for the AgentScope distributed model to further improve operational efficiency.
#
# Basic Concepts
# --------------
#
#
# Before diving into the advanced usage, we must first cover some basic concepts of the AgentScope distributed model.
#
# - **Main Process**: The process where the AgentScope application resides is referred to as the main process. For example, the ``run`` function in the previous section runs in the main process. There will only be one main process in each AgentScope application.
# - **Agent Server Process**: The AgentScope agent server process is where the agent runs in distributed mode. For example, in the previous section, all agents in ``dist_agents`` run in the agent server process. There can be multiple AgentScope agent server processes. These processes can run on any network-reachable machine and numerous agents can run simultaneously within each agent server process.
# - **Child Mode**: In child mode, the agent server process is started by the main process as a child process. For example, in the previous section, each agent in ``dist_agents`` is actually a child process of the main process. This mode is the default mode, which means if you call the ``to_dist`` function without any parameters, it will use this mode.
# - **Independent Mode**: In independent mode, the agent servers are independent of the main process and need to be pre-started on the machine. Specific parameters must be passed to the ``to_dist`` function, and the usage method will be introduced in the following section.
#
# Using Independent Mode
# ----------------------
#
# Compared to child mode, independent mode can avoid the overhead of initializing child processes, thus reducing the delay at the beginning of execution. This can effectively improve efficiency for programs that make multiple calls to ``to_dist``.
#
# In independent mode, you need to pre-start the agent server processes on the machine and pass specific parameters to the ``to_dist`` function. Here, we will continue using the example from the basic usage section, assuming the code file for the basic usage is ``dist_main.py``. Then, create and run the following script separately.
#
# .. code-block:: python
#
#     # Please do not run this code in a jupyter notebook.
#     # Copy this code into a file named ``dist_server.py`` and run with the command ``python dist_server.py``.
#     # Please install the distributed version of agentscope before running this code.
#     # pip install agentscope[distributed]
#
#     from dist_main import WebAgent
#     import agentscope
#
#     if __name__ == "__main__":
#         agentscope.init()
#         assistant_server_launcher = RpcAgentServerLauncher(
#             host="localhost",
#             port=12345,
#             custom_agent_classes=[WebAgent],
#         )
#         assistant_server_launcher.launch(in_subprocess=False)
#         assistant_server_launcher.wait_until_terminate()
#
#
# This script starts the AgentScope agent server process in the ``dist_server.py`` file, which is located in the same directory as the ``dist_main.py`` file from the basic usage section. Also, we need to make some minor modifications to the ``dist_main.py`` file by adding a new ``init_with_dist_independent`` function and replacing the call to ``init_with_dist`` with this new function.
#
# .. code-block:: python
#
#     def init_with_dist_independent():
#         return [WebAgent(f"W{i}").to_dist(host="localhost", port=12345) for i in range(len(URLS))]
#
#     if __name__ == "__main__":
#         agentscope.init()
#         start = time.time()
#         simple_agents = init_without_dist()
#         dist_agents = init_with_dist_independent()
#         end = time.time()
#         print(f"Time taken for initialization: {end - start}")
#         print(f"Time taken without distributed mode: {run(simple_agents)}")
#         print(f"Time taken with distributed mode: {run(dist_agents)}")
#
#
# After completing the modifications, open a command prompt and run the ``dist_server.py`` file. Once it is successfully started, open another command prompt and run the ``dist_main.py`` file.
#
# At this point, the initialization time in the output of ``dist_main.py`` will be significantly reduced. For example, the time taken here is only 0.02 seconds.
#
# .. code-block:: text
#
#     Time taken for initialization: 0.018129825592041016
#     ...
#
#
# It's important to note that the above example uses ``host="localhost"`` and ``port=12345``, and both ``dist_main.py`` and ``dist_server.py`` are running on the same machine. In actual usage, ``dist_server.py`` can run on a different machine. In this case, ``host`` should be set to the IP address of the machine running ``dist_server.py``, and ``port`` should be set to any available port, ensuring that different machines can communicate over the network.
#
# Avoid Duplicate Initialization
# ------------------------------
#
# In the code above, the ``to_dist`` function is called on an already initialized agent. The essence of ``to_dist`` is to clone the original agent to the agent server process, while retaining an ``RpcAgent`` in the main process as a proxy of the original agent. Calls to this ``RpcAgent`` will be forwarded to the corresponding agent in the agent server process.
#
# There is a potential issue with this approach: the original Agent is initialized twice—once in the main process and once in the agent server process—and these initializations are executed sequentially, which cannot be accelerated via parallelism. For Agents with low initialization costs, directly calling the ``to_dist`` function won't significantly affect performance. However, for agents with high initialization costs, it is important to avoid redundant initialization. Therefore, the AgentScope distributed mode offers an alternative method for distributed mode initialization, which allows directly passing the ``to_dist`` parameter within any Agent's initialization function, as shown in the modified example below:
#
# .. code-block:: python
#
#     def init_with_dist():
#         return [WebAgent(f"W{i}", to_dist=True) for i in range(len(URLS))]
#
#
#     def init_with_dist_independent():
#         return [WebAgent(f"W{i}", to_dist={"host": "localhost", "port": "12345"}) for i in range(len(URLS))]
#
#
# For the subprocess mode, you only need to pass ``to_dist=True`` in the initialization function. For the independent process mode, you need to pass the parameters that were originally passed to the ``to_dist`` function as a dictionary to the ``to_dist`` field.
