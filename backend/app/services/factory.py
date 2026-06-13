"""存储适配器工厂 — 根据类型创建对应适配器（延迟导入 SDK）"""
from app.services.base import BaseStorageAdapter
from app.schemas.schemas import StorageTypeInfo


def create_adapter(storage_type: str, config: dict) -> BaseStorageAdapter:
    """延迟导入：只在实际创建时才 import 对应的 SDK"""
    adapter_map = {
        "aliyun": "app.services.adapters.aliyun.AliyunOSSAdapter",
        "huawei": "app.services.adapters.huawei.HuaweiOBSAdapter",
        "tencent": "app.services.adapters.tencent.TencentCOSAdapter",
        "baidu": "app.services.adapters.baidu.BaiduBOSAdapter",
        "upyun": "app.services.adapters.upyun.UpyunUSSAdapter",
        "qiniu": "app.services.adapters.qiniu.QiniuKodoAdapter",
        "volcengine": "app.services.adapters.volcengine.VolcengineTOSAdapter",
        "local": "app.services.adapters.local.LocalStorageAdapter",
    }
    path = adapter_map.get(storage_type)
    if not path:
        raise ValueError(f"不支持的存储类型: {storage_type}")
    module_path, class_name = path.rsplit(".", 1)
    try:
        import importlib
        module = importlib.import_module(module_path)
    except ImportError:
        sdk_map = {
            "aliyun": "oss2",
            "huawei": "esdk-obs-python",
            "tencent": "cos-python-sdk-v5",
            "baidu": "bce-python-sdk",
            "qiniu": "qiniu",
            "volcengine": "tos",
        }
        pkg = sdk_map.get(storage_type, "未知")
        raise ImportError(f"请先安装 {storage_type} 的 SDK: pip install {pkg}")
    cls = getattr(module, class_name)
    return cls(config)


# 存储类型配置字段定义
STORAGE_TYPE_FIELDS = {
    "aliyun": {
        "type": "aliyun",
        "name": "阿里云 OSS",
        "fields": [
            {"key": "access_key_id", "label": "AccessKey ID", "required": True},
            {"key": "access_key_secret", "label": "AccessKey Secret", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True},
            {"key": "endpoint", "label": "Endpoint", "required": True, "type": "select", "options": [
                {"value": "oss-cn-hangzhou.aliyuncs.com", "label": "华东1(杭州)"},
                {"value": "oss-cn-shanghai.aliyuncs.com", "label": "华东2(上海)"},
                {"value": "oss-cn-beijing.aliyuncs.com", "label": "华北2(北京)"},
                {"value": "oss-cn-shenzhen.aliyuncs.com", "label": "华南1(深圳)"},
                {"value": "oss-cn-guangzhou.aliyuncs.com", "label": "华南2(广州)"},
                {"value": "oss-cn-hongkong.aliyuncs.com", "label": "中国香港"},
                {"value": "oss-us-west-1.aliyuncs.com", "label": "美国(硅谷)"},
                {"value": "oss-ap-southeast-1.aliyuncs.com", "label": "新加坡"},
                {"value": "oss-ap-northeast-1.aliyuncs.com", "label": "日本(东京)"},
                {"value": "oss-eu-central-1.aliyuncs.com", "label": "德国(法兰克福)"},
            ]},
            {"key": "custom_domain", "label": "自定义域名", "required": False, "placeholder": "https://files.example.com"},
            {"key": "prefix", "label": "路径前缀", "required": False, "placeholder": "files"},
        ],
    },
    "huawei": {
        "type": "huawei",
        "name": "华为云 OBS",
        "fields": [
            {"key": "access_key_id", "label": "Access Key ID", "required": True},
            {"key": "access_key_secret", "label": "Secret Access Key", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True},
            {"key": "endpoint", "label": "Endpoint", "required": True, "type": "select", "options": [
                {"value": "obs.cn-north-4.myhuaweicloud.com", "label": "华北-北京四"},
                {"value": "obs.cn-north-1.myhuaweicloud.com", "label": "华北-北京一"},
                {"value": "obs.cn-east-3.myhuaweicloud.com", "label": "华东-上海一"},
                {"value": "obs.cn-east-2.myhuaweicloud.com", "label": "华东-上海二"},
                {"value": "obs.cn-south-1.myhuaweicloud.com", "label": "华南-广州"},
                {"value": "obs.cn-southwest-2.myhuaweicloud.com", "label": "西南-贵阳一"},
                {"value": "obs.ap-southeast-1.myhuaweicloud.com", "label": "中国香港"},
                {"value": "obs.ap-southeast-3.myhuaweicloud.com", "label": "新加坡"},
                {"value": "obs.ap-southeast-2.myhuaweicloud.com", "label": "亚太-曼谷"},
                {"value": "obs.af-south-1.myhuaweicloud.com", "label": "非洲-约翰内斯堡"},
            ]},
            {"key": "custom_domain", "label": "自定义域名", "required": False},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "tencent": {
        "type": "tencent",
        "name": "腾讯云 COS",
        "fields": [
            {"key": "secret_id", "label": "SecretId", "required": True},
            {"key": "secret_key", "label": "SecretKey", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True, "placeholder": "example-1250000000"},
            {"key": "region", "label": "Region", "required": True, "placeholder": "ap-guangzhou"},
            {"key": "custom_domain", "label": "自定义域名", "required": False},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "baidu": {
        "type": "baidu",
        "name": "百度云 BOS",
        "fields": [
            {"key": "access_key_id", "label": "Access Key ID", "required": True},
            {"key": "access_key_secret", "label": "Secret Access Key", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True},
            {"key": "endpoint", "label": "Endpoint", "required": True, "type": "select", "options": [
                {"value": "bj.bcebos.com", "label": "北京"},
                {"value": "gz.bcebos.com", "label": "广州"},
                {"value": "su.bcebos.com", "label": "苏州"},
                {"value": "bd.bcebos.com", "label": "保定"},
                {"value": "hkg.bcebos.com", "label": "中国香港"},
                {"value": "sin.bcebos.com", "label": "新加坡"},
            ]},
            {"key": "custom_domain", "label": "自定义域名", "required": False},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "upyun": {
        "type": "upyun",
        "name": "又拍云 USS",
        "fields": [
            {"key": "operator_name", "label": "操作员名称", "required": True},
            {"key": "operator_password", "label": "操作员密码", "required": True, "secret": True},
            {"key": "bucket_name", "label": "服务名称", "required": True},
            {"key": "domain", "label": "加速域名", "required": False, "placeholder": "https://example.upaiyun.com"},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "qiniu": {
        "type": "qiniu",
        "name": "七牛云 Kodo",
        "fields": [
            {"key": "access_key", "label": "AccessKey", "required": True},
            {"key": "secret_key", "label": "SecretKey", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True},
            {"key": "custom_domain", "label": "自定义域名", "required": False, "placeholder": "https://files.example.com"},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "volcengine": {
        "type": "volcengine",
        "name": "火山引擎 TOS",
        "fields": [
            {"key": "access_key_id", "label": "Access Key ID", "required": True},
            {"key": "access_key_secret", "label": "Secret Access Key", "required": True, "secret": True},
            {"key": "bucket_name", "label": "Bucket 名称", "required": True},
            {"key": "endpoint", "label": "Endpoint", "required": True, "type": "select", "options": [
                {"value": "tos-cn-beijing.volces.com", "label": "华北-北京"},
                {"value": "tos-cn-shanghai.volces.com", "label": "华东-上海"},
                {"value": "tos-cn-guangzhou.volces.com", "label": "华南-广州"},
                {"value": "tos-cn-chengdu.volces.com", "label": "西南-成都"},
                {"value": "tos-cn-hongkong.volces.com", "label": "中国香港"},
                {"value": "tos-ap-singapore.volces.com", "label": "新加坡"},
            ]},
            {"key": "region", "label": "Region", "required": True, "placeholder": "cn-beijing"},
            {"key": "custom_domain", "label": "自定义域名", "required": False},
            {"key": "prefix", "label": "路径前缀", "required": False},
        ],
    },
    "local": {
        "type": "local",
        "name": "本地文件系统",
        "fields": [
            {"key": "root_path", "label": "根目录路径", "required": True, "placeholder": "/data/files"},
        ],
    },
}
