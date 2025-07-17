# 飞书API客户端

import json
import asyncio
import httpx
from rich.console import Console

console = Console()

class FeishuClient:
    """飞书API客户端
    
    用于与飞书API交互，支持文档更新等功能
    """
    
    def __init__(self):
        # 飞书API配置
        self.app_id = "cli_a75f9be734fb900d"
        self.app_secret = "lMEN0kvfXJOPwkaU1x9fhea8vKSlRSWi"
        self.tenant_access_token = ""
        self.base_url = "https://open.feishu.cn/open-apis"
        
    async def get_tenant_access_token(self):
        """获取租户访问令牌
        
        Returns:
            str: 租户访问令牌
        """
        if not self.app_id or not self.app_secret:
            console.print("[yellow]警告: 飞书API凭证未配置，请在配置文件中设置app_id和app_secret")
            return None
            
        try:
            url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
            payload = {
                "app_id": self.app_id,
                "app_secret": self.app_secret
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                data = response.json()
                
                if data.get("code") == 0:
                    self.tenant_access_token = data.get("tenant_access_token")
                    return self.tenant_access_token
                else:
                    console.print(f"[red]获取飞书访问令牌失败: {data}")
                    return None
        except Exception as e:
            console.print(f"[red]获取飞书访问令牌时出错: {str(e)}")
            return None
    
    async def update_document(self, doc_id, content):
        """更新飞书文档内容
        
        Args:
            doc_id: 文档ID
            content: 要更新的内容
            
        Returns:
            bool: 更新是否成功
        """
        if not doc_id:
            console.print("[yellow]警告: 未提供文档ID，无法更新文档")
            return False
            
        try:
            # 确保有有效的访问令牌
            if not self.tenant_access_token:
                await self.get_tenant_access_token()
                
            if not self.tenant_access_token:
                return False
                
            # 构建更新文档的请求
            url = f"{self.base_url}/doc/v2/documents/{doc_id}/content"
            headers = {
                "Authorization": f"Bearer {self.tenant_access_token}",
                "Content-Type": "application/json"
            }
            
            # 构建文档内容更新请求
            payload = {
                "content": content
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(url, json=payload, headers=headers)
                data = response.json()
                
                if data.get("code") == 0:
                    console.print("[green]飞书文档更新成功")
                    return True
                else:
                    console.print(f"[red]飞书文档更新失败: {data}")
                    return False
                    
        except Exception as e:
            console.print(f"[red]更新飞书文档时出错: {str(e)}")
            return False


if __name__ == "__main__":
    # 测试代码
    async def test():
        client = FeishuClient()
        # 设置测试用的文档ID
        doc_id = "your_test_doc_id"
        # 测试更新文档
        result = await client.update_document(doc_id, "这是通过API更新的测试内容")
        print(f"文档更新结果: {result}")
    
    asyncio.run(test())