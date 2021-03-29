from django.core.files.storage import Storage
from django.conf import settings


class FasfDFSStorage(Storage):
    """自定义文件存储类"""
    def __init__(self, fdfs_base_url=None):
        # if not fdfs_base_url:
        #     self.fdfd_base_url = settings.FDFD_BASE_URL
        # # else:
        # self.fdfd_base_url = fdfs_base_url
        self.fdfs_base_url = fdfs_base_url or settings.FDFD_BASE_URL

    def open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        pass

    def url(self, name):
        """
        返回文件全部路径
        :param name: 文件路径  数据库内的相对路径
        :return: 完整路径 ip:port+name
        """
        return self.fdfs_base_url +name