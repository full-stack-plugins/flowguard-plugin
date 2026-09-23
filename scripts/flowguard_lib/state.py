"""状态锁与原子写工具；项目流程事实保存在 docs/（十阶段文档为唯一事实源）。"""
import contextlib
import fcntl
import os
import pathlib
import stat
import tempfile


class StateError(Exception):
    pass


@contextlib.contextmanager
def state_lock(root):
    """fcntl 独占锁（LOCK_NB），锁冲突快速失败。"""
    from .runtime import repository_state_dir
    lock = repository_state_dir(root, create=True) / ".lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    fh = lock.open("w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise StateError("状态文件被其它进程锁定，请稍后重试")
    try:
        yield
    finally:
        fh.close()


def atomic_write_text(path, content):
    """同目录临时文件替换文档；写入或替换失败时保留旧正文。"""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    fd, temporary = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)


def atomic_create_text(path, content, *, mode=None):
    """原子创建新文档，不覆盖并发创建的目标，也不留下半写文件。"""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".fg-atomic-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.link(temporary, path)
    finally:
        pathlib.Path(temporary).unlink(missing_ok=True)
