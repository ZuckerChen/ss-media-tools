"""
发布功能测试脚本
用于测试发布管理模块的各项功能
"""
import requests
import json
from datetime import datetime, timedelta


class PublishTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def call_api(self, endpoint, method="GET", data=None):
        """调用API接口"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            
            return {
                "success": response.status_code < 400,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def test_platforms_list(self):
        """测试获取平台列表"""
        print("\n=== 测试获取平台列表 ===")
        result = self.call_api("/api/publish/platforms")
        
        if result["success"]:
            platforms = result["data"]
            print(f"✅ 成功获取 {len(platforms)} 个平台:")
            for platform in platforms:
                print(f"  - {platform['name']} ({platform['platform']}): 最大{platform['max_length']}字")
        else:
            print(f"❌ 失败: {result.get('error', '未知错误')}")
        
        return result["success"]
    
    def test_add_platform_account(self):
        """测试添加平台账号"""
        print("\n=== 测试添加平台账号 ===")
        
        # 添加微博测试账号
        weibo_data = {
            "platform": "weibo",
            "account_name": "测试微博账号",
            "account_id": "test_weibo_123",
            "access_token": "test_token_weibo"
        }
        
        result = self.call_api("/api/publish/accounts", "POST", weibo_data)
        if result["success"]:
            print("✅ 微博账号添加成功")
        else:
            print(f"❌ 微博账号添加失败: {result.get('error')}")
        
        # 添加微信测试账号
        wechat_data = {
            "platform": "wechat",
            "account_name": "测试微信公众号",
            "account_id": "test_wechat_456",
            "access_token": "test_token_wechat"
        }
        
        result2 = self.call_api("/api/publish/accounts", "POST", wechat_data)
        if result2["success"]:
            print("✅ 微信账号添加成功")
        else:
            print(f"❌ 微信账号添加失败: {result2.get('error')}")
        
        return result["success"] and result2["success"]
    
    def test_get_accounts(self):
        """测试获取账号列表"""
        print("\n=== 测试获取账号列表 ===")
        result = self.call_api("/api/publish/accounts")
        
        if result["success"]:
            accounts = result["data"]
            print(f"✅ 成功获取 {len(accounts)} 个账号:")
            for account in accounts:
                print(f"  - {account['account_name']} ({account['platform']})")
        else:
            print(f"❌ 失败: {result.get('error')}")
        
        return result["success"]
    
    def test_create_test_draft(self):
        """创建测试草稿"""
        print("\n=== 创建测试草稿 ===")
        
        draft_data = {
            "title": "发布功能测试文章",
            "content": "这是一篇用于测试发布功能的文章。文章内容包含了各种测试要素，用来验证发布到不同平台的适配性和功能正确性。",
            "category": "测试",
            "tags": "测试,发布,功能验证",
            "platform_type": "通用"
        }
        
        result = self.call_api("/api/drafts", "POST", draft_data)
        if result["success"]:
            draft_id = result["data"]["id"]
            print(f"✅ 测试草稿创建成功，ID: {draft_id}")
            return draft_id
        else:
            print(f"❌ 草稿创建失败: {result.get('error')}")
            return None
    
    def test_content_check(self, draft_id):
        """测试内容适配检查"""
        print("\n=== 测试内容适配检查 ===")
        
        # 获取草稿内容
        draft_result = self.call_api(f"/api/drafts/{draft_id}")
        if not draft_result["success"]:
            print("❌ 无法获取草稿内容")
            return False
        
        draft = draft_result["data"]
        
        # 检查所有平台适配性
        check_data = {
            "title": draft["title"],
            "content": draft["content"],
            "platform": "all"
        }
        
        result = self.call_api("/api/publish/check", "POST", check_data)
        if result["success"]:
            suggestions = result["data"]["platform_suggestions"]
            print("✅ 内容适配检查结果:")
            
            for platform, suggestion in suggestions.items():
                status = "✅" if suggestion["valid"] else "❌"
                print(f"  {status} {suggestion['platform_name']}: {suggestion['optimization']}")
                if not suggestion["valid"]:
                    print(f"     错误: {suggestion['error']}")
            
            return True
        else:
            print(f"❌ 检查失败: {result.get('error')}")
            return False
    
    def test_publish_content(self, draft_id):
        """测试内容发布"""
        print("\n=== 测试内容发布 ===")
        
        # 立即发布到微博和微信
        publish_data = {
            "draft_id": draft_id,
            "platforms": ["weibo", "wechat"],
            "publish_time": None
        }
        
        result = self.call_api("/api/publish", "POST", publish_data)
        if result["success"]:
            result_data = result["data"]
            print(f"✅ 发布结果: {result_data['summary']}")
            
            for platform, result_detail in result_data["results"].items():
                if result_detail["success"]:
                    print(f"  ✅ {platform}: 发布成功")
                    if result_detail.get("platform_post_id"):
                        print(f"     平台ID: {result_detail['platform_post_id']}")
                else:
                    print(f"  ❌ {platform}: {result_detail['error']}")
            
            return True
        else:
            print(f"❌ 发布失败: {result.get('error')}")
            return False
    
    def test_scheduled_publish(self, draft_id):
        """测试定时发布"""
        print("\n=== 测试定时发布 ===")
        
        # 安排5分钟后发布
        future_time = datetime.now() + timedelta(minutes=5)
        
        publish_data = {
            "draft_id": draft_id,
            "platforms": ["weibo"],
            "publish_time": future_time.isoformat()
        }
        
        result = self.call_api("/api/publish", "POST", publish_data)
        if result["success"]:
            print("✅ 定时发布任务创建成功")
            return True
        else:
            print(f"❌ 定时发布失败: {result.get('error')}")
            return False
    
    def test_publish_records(self):
        """测试获取发布记录"""
        print("\n=== 测试获取发布记录 ===")
        
        result = self.call_api("/api/publish/records")
        if result["success"]:
            records_data = result["data"]
            records = records_data["records"]
            print(f"✅ 成功获取 {len(records)} 条发布记录:")
            
            for record in records[:3]:  # 只显示前3条
                status_icon = {"success": "✅", "failed": "❌", "scheduled": "⏰"}.get(record["status"], "⚪")
                print(f"  {status_icon} {record['title']} -> {record['platform']} ({record['status']})")
            
            return True
        else:
            print(f"❌ 获取记录失败: {result.get('error')}")
            return False
    
    def test_publish_stats(self):
        """测试获取发布统计"""
        print("\n=== 测试获取发布统计 ===")
        
        result = self.call_api("/api/publish/stats")
        if result["success"]:
            stats = result["data"]
            print("✅ 发布统计获取成功:")
            
            # 平台统计
            if stats.get("platform_stats"):
                print("  平台统计:")
                for stat in stats["platform_stats"]:
                    print(f"    {stat['platform']}: {stat['total']}次 (成功率{stat['success_rate']}%)")
            
            # 日期统计
            if stats.get("daily_stats"):
                print(f"  最近7天发布: {len(stats['daily_stats'])}天有记录")
            
            return True
        else:
            print(f"❌ 获取统计失败: {result.get('error')}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始发布功能测试...")
        
        results = []
        
        # 1. 测试平台列表
        results.append(self.test_platforms_list())
        
        # 2. 测试添加账号
        results.append(self.test_add_platform_account())
        
        # 3. 测试获取账号
        results.append(self.test_get_accounts())
        
        # 4. 创建测试草稿
        draft_id = self.test_create_test_draft()
        if draft_id:
            results.append(True)
            
            # 5. 测试内容检查
            results.append(self.test_content_check(draft_id))
            
            # 6. 测试立即发布
            results.append(self.test_publish_content(draft_id))
            
            # 7. 测试定时发布
            results.append(self.test_scheduled_publish(draft_id))
        else:
            results.extend([False, False, False, False])
        
        # 8. 测试发布记录
        results.append(self.test_publish_records())
        
        # 9. 测试发布统计
        results.append(self.test_publish_stats())
        
        # 汇总结果
        success_count = sum(results)
        total_count = len(results)
        
        print(f"\n{'='*50}")
        print(f"🎯 测试完成: {success_count}/{total_count} 项测试通过")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print("🎉 所有测试通过！发布功能运行正常")
        else:
            print("⚠️  部分测试失败，请检查相关功能")
        
        return success_count == total_count


if __name__ == "__main__":
    # 检查API服务是否运行
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API服务正常运行")
            
            # 运行测试
            tester = PublishTester()
            tester.run_all_tests()
        else:
            print("❌ API服务异常")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保后端服务已启动")
        print("   运行命令: python main.py")
    except Exception as e:
        print(f"❌ 测试运行错误: {e}") 