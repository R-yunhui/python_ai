import os
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

# 创建一个 fastapi 示例
app = FastAPI(
    title="FastAPI Demo",
    description="A FastAPI demonstration app",
    version="1.0",
)


# 创建一个实体类，通过 Pydantic 进行简单的测试
class Item(BaseModel):
    name: str = Field(description="名称", max_length=20, min_length=1)
    price: float = Field(description="价格", gt=0, lt=1000)
    description: str = Field(description="描述", max_length=100)
    tags: list[str] = Field(description="标签", min_length=1)

    def __str__(self):
        return f"Item(name={self.name}, price={self.price}, description={self.description}, tags={self.tags})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"name": self.name, "price": self.price, "description": self.description, "tags": self.tags}


@app.get(
    path="/hello",
    tags=["hello world"],
)
def hello_world() -> str:
    """
    这是一个简单的 hello world 接口
    :return: "Hello World!"
    """
    return "Hello World!"


@app.post(
    path="/create_item",
    tags=["create_item"],
)
def create_item(item: Item) -> Item:
    """
    创建一个新的 item
    :param item: 要创建的 item
    :return: 创建的 item
    """
    return item


@app.get(
    path="/get_item",
    tags=["get_item"],
)
def get_item(item_id: int) -> Item:
    """
    获取一个 item
    :param item_id: item 的 id
    :return: item
    """
    if item_id < 0:
        raise HTTPException(status_code=404, detail="Item Id must be greater than or equal to 0")

    return Item(name="item1", price=100, description="item1 description", tags=["tag1", "tag2"])


FILE_DIR_PATH = os.path.join(os.getcwd(), "data")


def create_dir():
    if not os.path.exists(FILE_DIR_PATH):
        os.makedirs(FILE_DIR_PATH)
        print(f"目录 {FILE_DIR_PATH} 创建成功")
    else:
        print(f"目录 {FILE_DIR_PATH} 已存在")


@app.post(
    path="/upload_file",
    tags=["upload_file"],
    description="上传单个文件"
)
async def upload_file(file: UploadFile = File(..., max_size=1024 * 1024 * 10)) -> dict[str, str]:  # 限制单个文件最大10MB
    """
    上传单个文件
    :param file: 要上传的文件
    :return: 上传结果（包含原文件名和保存路径）
    """
    try:
        # 处理文件名（防路径穿越 + 防覆盖）
        filename = os.path.basename(file.filename)  # 去除路径部分，避免../../等恶意路径
        unique_id = uuid.uuid4().hex  # 生成唯一ID
        safe_filename = f"{unique_id}_{filename}"
        file_path = os.path.join(FILE_DIR_PATH, safe_filename)

        # 分块写入文件（适合大文件，减少内存占用）
        with open(file_path, "wb") as f:
            while contents := await file.read(1024 * 1024):  # 每次读取1MB
                f.write(contents)

        return {
            "original_filename": filename,
            "saved_filename": safe_filename,
            "message": "上传成功"
        }
    except Exception as e:
        # 捕获异常并返回友好错误信息
        raise HTTPException(status_code=500, detail=f"文件上传失败：{str(e)}")


@app.post(
    path="/upload_files",
    tags=["upload_files"],
    description="上传多个文件"
)
async def upload_files(files: list[UploadFile] = File(..., max_size=1024 * 1024 * 10)) -> list[dict]:  # 单个文件最大10MB
    """
    上传多个文件
    :param files: 要上传的文件列表
    :return: 所有文件的上传结果列表
    """
    results = []
    for file in files:
        try:
            # 调用单文件上传接口处理每个文件，并收集结果
            result = await upload_file(file)
            results.append(result)
        except Exception as e:
            # 单个文件失败不影响其他文件，记录错误信息
            results.append({
                "original_filename": os.path.basename(file.filename),
                "message": f"上传失败：{e.detail}"
            })
    return results


@app.get("/download/{file_name}")
async def download_file(file_name: str):
    """
    根据文件名下载文件
    :param file_name: 要下载的文件名
    :return: 文件响应
    """
    # 构建文件完整路径
    file_path = os.path.join(FILE_DIR_PATH, file_name)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        return {"error": "文件不存在"}

    # 返回文件（自动处理 MIME 类型和下载头）
    return FileResponse(
        path=file_path,
        filename=file_name,  # 客户端下载时显示的文件名
        media_type="application/octet-stream"  # 通用二进制流类型
    )


@app.get("/download-large/{file_name}")
async def download_large_file(file_name: str):
    """
    根据文件名下载大文件（支持流式传输）
    :param file_name: 要下载的文件名
    :return: 流式传输的文件响应
    """
    file_path = os.path.join(FILE_DIR_PATH, file_name)
    if not os.path.exists(file_path):
        return {"error": "文件不存在"}

    # 流式传输文件（支持断点续传）
    return StreamingResponse(
        file_streamer(file_path),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file_name}"  # 指定下载文件名
        },
        # 可选：文件传输完成后执行清理任务（如删除临时文件）
        background=BackgroundTask(lambda: print(f"文件 {file_name} 下载完成"))
    )


def file_streamer(file_path):
    """生成器：分块读取文件内容"""
    with open(file_path, "rb") as f:
        while chunk := f.read(1024 * 1024):  # 每次读取 1MB
            yield chunk


if __name__ == "__main__":
    import uvicorn

    print("uvicorn started...")
    print("http://127.0.0.1:8000/docs")

    # 确保存储文件的目录一定存在
    create_dir()

    uvicorn.run(app, host="0.0.0.0", port=8000)
