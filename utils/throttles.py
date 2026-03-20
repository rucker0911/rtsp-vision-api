from rest_framework.throttling import SimpleRateThrottle


class LoginRateThrottle(SimpleRateThrottle):
    """依 IP 限制登入嘗試頻率，防止暴力破解。頻率由 DEFAULT_THROTTLE_RATES['login'] 控制。"""

    scope = "login"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
