import multiprocessing as mp

from logger import Logger, MemoryHandler


def child() -> None:
    log = Logger.get_instance()  # a brand-new Logger: this process has its own memory
    print(f"child : handlers configured = {len(log.handlers)}")
    log.info("hello from the child")  # no handlers here, so this goes nowhere


if __name__ == "__main__":
    mp.set_start_method("spawn")
    memory = MemoryHandler()
    log = Logger.get_instance()
    log.add_handler(memory)
    log.info("hello from the parent")

    process = mp.Process(target=child)
    process.start()
    process.join()

    print(f"parent: handlers configured = {len(log.handlers)}")
    print(f"parent: lines received      = {len(memory.lines)}")
