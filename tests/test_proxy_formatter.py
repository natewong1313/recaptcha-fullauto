  
import unittest

class ProxyTest(unittest.TestCase):
    def test_proxy_formatter(self):
        proxy = "127.0.0.1:8888:nate:test"
        proxy_split = proxy.split(":")
        if len(proxy_split) == 2:
            formatted_proxy = {
                "ip": proxy_split[0], 
                "port": int(proxy_split[1])
            }
        else:
            formatted_proxy = {
                "ip": proxy_split[0], 
                "port": int(proxy_split[1]),
                "user": proxy_split[2], 
                "pass": proxy_split[3]
            }
        self.assertEqual(formatted_proxy["ip"], "127.0.0.1")
        self.assertEqual(formatted_proxy["port"], 8888)
        self.assertEqual(formatted_proxy["user"], "nate")
        self.assertEqual(formatted_proxy["pass"], "test")


if __name__ == "__main__":
    unittest.main() 