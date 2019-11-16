from factorio_balancers import Balancer
from factorio_balancers.balancer import (
    IllegalEntities, IllegalConfigurations, IllegalConfiguration)
from test_textures import TEXTURES

strings = (
    ("lane balancer with false inputs", '0eNqVlN1uwyAMhd/F17TCJPQnr1JNU9KiCSkhCNxpUZR3L0m0aVK9NVwhg/k4B4NHaNq78cE6gmoEe+1dhOoyQrQfrm7nORq8gQosmQ4EuLqbIwq1i74PtGtMSzAJsO5mvqDC6U2AcWTJmpW0BMO7u3eNCSnhL4YA38e0rXfzqQm1S6lDGoppEk8Y9YOJvrVEae4ZIPd6RSgOUWQrQQ5Tbseob4yAmw3muq4pBqo3Q+U/0g6bKcgqOzDMY65dySk75VJYf+fcCsrX/lDmvCxWFmJm9eTrB4Eqs5bstWORSeH9lbn3zn5h1LmY9I1Td1k6UfWrcQn4NCEu2cdC4llrfSqT/wcmYJ47'),
    ("straight 4 belts", '0eNqV0s0KgzAMB/B3+Z8r+DXFvsoYQ7cwCppKW8dE+u6r7jJYd+gxIf0lNNkwjAvNRrGD3KBumi3keYNVD+7HPefWmSChHE0Q4H7aI2d6trM2LhtodPACiu/0giz8RYDYKafoIx3BeuVlGsiEgn+GwKxteKZ57xqoXGCFzCrvxY9SpiplTKlSlSKm1IlKHkNOiUh0kiYRCZ8StnVsVn4dgsCTjD2K2yovurqs26bz/g1KFrro'),
    ("4-4 balancer", '0eNqVld1ugzAMhd/F1+kUJxQor1JNU3+iKhINKIRpVcW7L8DWVcNt4ysIJB/2OTa+wr7uTeutC1BdwR4a10G1vUJnT25Xj8/CpTVQgQ3mDALc7jyugt+5rm18WO1NHWAQYN3RfEGFg3h5uGtrG4Lxd8fU8C7AuGCDNXMA0+Ly4frzPu6scHlaQNt08UDjxi9FyArf1gIu8SYbxjD+IVQCQj4l6Ef5L0NRM0ZTmIyNURRmnY7BX4yAo/XmML/LCWh+g/bRGX/yTby+wOqI/TG66UPbj/WwABfJ0eIT6UouhVRuk0yRpHCKYKJkKCcZwiFyfZZUzqi4VScTktYpbXlrKiQDy5ieytdVjGumw7RkOVcyOsGCiyGLFkt+a+JfgVn3qL42HA/J0JRkWkhTkEkh1VaK3YcpKinNGUDkv0tljAEUCXEiTnOzupvRAj6N76bthZaYl1JrVQ7DN97ElM8='),
    ("simple lane balander", '0eNqV021rgzAQB/Dvcq9jSdTqzFcpY2h7jICeIbmOieS7NyqMQTPWvMyDv9xf7lYYxjtaZ4hBr2CuM3nQlxW8+aR+3PZ4sQgaDOMEAqifthW7nrydHRcDjgxBgKEbfoNW4V0AEhs2eEj7Yvmg+zSgixf+MgTY2cfPZtpejZQUsIAuqhDEk1LmKmVKqV5WCnUwKia9GYfX46xMoHUuKlOlnXMDqpTSvKyk8zUJs800k/HeMuPJ/+vqfkhvR8Mc956x03nnkj9Lycyikj2lchs89nccmX289K9pFPCFzu+X20qqri7rtulCeAD8hTw6'),
)


for name, string in strings:
    try:
        balancer = Balancer(string, print2d=True, textures=TEXTURES)
    except (IllegalConfigurations, IllegalEntities,
            IllegalConfiguration) as e:
        print(repr(e))
    else:
        print("No Exceptions")
