# 模拟 py 的 io密集型和cpu密集型任务
import multiprocessing
import threading
import time

import requests

from concurrent.futures import ThreadPoolExecutor

def cpu_task():
    """
    cpu密集型任务
    """
    total = 0
    for _ in range(10**7):
        total += 1
    return total


# 多线程
def multithread_example():
    """
    多线程执行cpu密集型任务
    """
    threads = []
    for _ in range(4): # 创建4个线程操作
        thread = threading.Thread(target=cpu_task)
        threads.append(thread)
        thread.start() # 启动线程

    for t in threads:
        t.join() # 等待线程执行完毕


# 多进程
def multiprocessing_example():
    processes = []
    for _ in range(4):  # 创建 4 个进程
        p = multiprocessing.Process(target=cpu_task)
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


def request_example():
    """
    模拟io密集型任务
    """
    url = "https://api.siliconflow.cn/v1/chat/completions"

    headers = {
        "Authorization": "Bearer sk-yrihggiycevxjuwibdgsloznaufddxrdvijtbfdmapevxirh",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "who are you？"
            }
        ]
    }

    """
    requests 库中的 timeout 参数单位是秒，可以是整数或浮点数。
        整数：表示超时时间为整秒。
        浮点数：支持精确到小数点后的秒数。
        元组：可以传入 (连接超时, 读取超时) 的元组，分别设置连接和读取的超时时间。
    """
    with requests.post(url, headers=headers, json=data, stream=True, timeout=(10, 60)) as response:
        if response.status_code == 200:
            # 按块读取响应内容
            """
            content 和 iter_content 是 requests 库中 Response 对象的两个方法/属性，用于处理 HTTP 响应内容。它们的主要区别如下：
                1. content
                类型: 属性。
                功能: 一次性读取整个响应内容，返回的是字节类型数据（bytes）。
                适用场景: 响应内容较小，可以直接加载到内存中。
                2. iter_content
                类型: 方法。
                功能: 按块（chunk）迭代读取响应内容，适合处理大文件或流式数据。
            """
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 忽略空块
                    print(chunk.decode('utf-8'))
        else:
            print(f"请求失败: {response.text}")

def task(name: int) -> str:
    """
    模拟任务
    """
    print(f"当前线程名称: {threading.current_thread().name}")
    print(f"任务 {name} 开始")
    time.sleep(2)  # 模拟耗时操作
    print(f"任务 {name} 完成")
    return "success"

def thread_pool_example():
    """
    线程池
    """
    with ThreadPoolExecutor(max_workers=10, thread_name_prefix='work_thread') as executor:
        futures = [executor.submit(task, i) for i in range(10)]
        for future in futures:
            print(f"任务结果: {future.result()}")


if __name__ == "__main__":
    # request_example()

    """
    Python 支持 CPU 并发，但由于其解释器的实现（特别是 CPython），存在 GIL（全局解释器锁） 的限制，这会影响多线程的并行执行。 Global Interpreter Lock，简称 GIL。

    GIL 的作用
        GIL 是 CPython 中的一种机制，用于确保同一时间只有一个线程执行 Python 字节码。它的存在主要是为了保护 CPython 的内存管理线程安全。
    
    对 CPU 并发的影响
        多线程：
        Python 的多线程（threading 模块）可以实现并发，但由于 GIL 的存在，线程无法真正利用多核 CPU 并行执行。
        多线程更适合 I/O 密集型任务（如网络请求、文件读写），因为 GIL 会在 I/O 操作时释放。
        
        多进程：
        Python 的多进程（multiprocessing 模块）不受 GIL 的限制，因为每个进程都有独立的 Python 解释器和 GIL。
        多进程适合 CPU 密集型任务（如计算密集型操作），可以充分利用多核 CPU。
    """
    # start = time.time()
    # multithread_example()
    # # 保留两位小数
    # print(f"多线程耗时: {time.time() - start:.2f} 秒")
    #
    # start = time.time()
    # multiprocessing_example()
    # print(f"多进程耗时: {time.time() - start:.2f} 秒")

    thread_pool_example()

