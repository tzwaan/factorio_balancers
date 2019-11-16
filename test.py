from factorio_balancers import Balancer
from factorio_balancers.balancer import IllegalEntities, IllegalConfigurations
from test_textures import TEXTURES


# has illegal entities
illegal = '0eNqlU+9qwjAQf5f7OOKwLSqEvcmQkrY3PTCXkqayInn3XeLmnG5zsi+Fy939/nE9QLMbsffEAfQBqHU8gH4+wEAbNrv0FqYeQQMFtKCAjU2V8RS2FgO1s9bZhtgE5yEqIO7wFXQR1U2MDlvq0H8PUMa1AuRAgfCoKBdTzaNt0AvDCSdpDobDOZCC3g2y6zjRC96sUjCBnguDzDO2qTekZpE+G4/I5zTUiQaZJd+OFHJZxHWMydeFkvI3R9dC5o+Lk5SO/FHJkcxx8G5XN7g1e5Jl2XiHrKXX0Unzh2VBSWu2Nz6zaXiC9NBPsjByqF+8szVxP8po8CPGe/wnwwrKH/vV3/KpblzNVUTlXQl9gl6ENGCq6y9ZuR4lqQwHDxD/cQ1lditHmo9an/1HCvboh8yxqubFcrkqy8UyxjeXay3C'

# has only legal entities
legal = '0eNqVld1ugzAMhd/F1+kUJxQor1JNU3+iKhINKIRpVcW7L8DWVcNt4ysIJB/2OTa+wr7uTeutC1BdwR4a10G1vUJnT25Xj8/CpTVQgQ3mDALc7jyugt+5rm18WO1NHWAQYN3RfEGFg3h5uGtrG4Lxd8fU8C7AuGCDNXMA0+Ly4frzPu6scHlaQNt08UDjxi9FyArf1gIu8SYbxjD+IVQCQj4l6Ef5L0NRM0ZTmIyNURRmnY7BX4yAo/XmML/LCWh+g/bRGX/yTby+wOqI/TG66UPbj/WwABfJ0eIT6UouhVRuk0yRpHCKYKJkKCcZwiFyfZZUzqi4VScTktYpbXlrKiQDy5ieytdVjGumw7RkOVcyOsGCiyGLFkt+a+JfgVn3qL42HA/J0JRkWkhTkEkh1VaK3YcpKinNGUDkv0tljAEUCXEiTnOzupvRAj6N76bthZaYl1JrVQ7DN97ElM8='

string2 = '0eNplj8EOgjAQRP9lztWABA39FWMI6IqbQNu0i5GQ/rstXoweZ3fnzeyKfpzJeTYCvYKv1gTo84rAg+nGPJPFETRYaIKC6aasghtZhDyiApsbvaDLeFEgIyxMH8YmltbMU58udfnvVnA2JIM1OSlBdsW+VligiwS2s7hZ2tTO+gRKRs/DQ5AjfxYj3QW5wFZTf32l8CQftoRTVZRNVTeH6hjjG/iUVHE='

# has a lane balancer
lane = '0eNqV021rgzAQB/Dvcq9jSdTqzFcpY2h7jICeIbmOieS7NyqMQTPWvMyDv9xf7lYYxjtaZ4hBr2CuM3nQlxW8+aR+3PZ4sQgaDOMEAqifthW7nrydHRcDjgxBgKEbfoNW4V0AEhs2eEj7Yvmg+zSgixf+MgTY2cfPZtpejZQUsIAuqhDEk1LmKmVKqV5WCnUwKia9GYfX46xMoHUuKlOlnXMDqpTSvKyk8zUJs800k/HeMuPJ/+vqfkhvR8Mc956x03nnkj9Lycyikj2lchs89nccmX289K9pFPCFzu+X20qqri7rtulCeAD8hTw6'

illegal_belt_configuration = '0eNqVktFqwzAMRf9Fz+5I0rRp/SuljKQVQ5AoxlbLQvC/T0lgDOpB/WQkS0dX9p2h6x/oPLGAnYFuIwewlxkCfXHbLzmZHIIFEhzAALfDEolvObjRy67DXiAaIL7jN9gyXg0gCwnhRlqD6ZMfQ4deC/5jGHBj0LaRl6mK2mnppEcVo3nBVG9jio1SqsY7ebxtV3WCuc9kFilhdfZ+ZQpzyMUkxRx/KcH1JKK51/7i47ASkjqazDdJftYpdxmlqI1Wy9k/DjXwRB/W6mZflOe6qpvjOcYf9HPtAg=='

illegal_underground_configuration = '0eNqVlN1uhCAQhd9lrtkE0GrlVZqm0V2yIVEw/DQ1hncvarJpu1idK4IMH4dzcGbo+iBHq7QHMYO6Gu1AvM3g1F23/fLNT6MEAcrLAQjodlhm3rbajcb6Syd7D5GA0jf5BYLFdwJSe+WV3EjrZPrQYeikTQV7DAKjcWmb0cupCXVJpVMaeKLflJXXba2M5AnKT0PpxiyOmcVpJssyqwyzfDBDssverUnj/0r/3p48AtFjWJx/OuQFK5zHDKVC58R+K+UZaI2F0uOcXrHZs2Nmg7WQ5SxkFB03RafNGFIrzUrl2GROpM0K9P13X7sJfs+AEvkAzijH/kMp/9T31h4pfrRUAp/SurW4LihrSl7WVRPjNwlg0w4='

illegal_underground_configuration2 = '0eNqV0l0KwjAMAOC75LnC1Lm5XkVENg1S2NLSduIYvbvpRBGcwz6FlPTrTzJC0/ZorCIPcgR11uRAHkZw6kp1G9f8YBAkKI8dCKC6i5m3NTmjrV812HoIAhRd8A5yHY4CkLzyCp/SlAwn6rsGLRf8MgQY7XibpngqUysuHWIIQXwxm1Qmm1O2fysLSJ6IzD9o97eSLSjFW+m5H/ZqNcdFJ+PevVpMpo+9/FLL1M+evds+8YWzSJX42YzwQE7DKz9mXcANrZuKy222rvJNXhZVCA+hFwbe'

illegal_splitter_configuration = '0eNqVld1uhCAQRt9lrrEB/NvlVZqm0V3SkCgaYJsaw7sXNW3a7LTLXIJ4PAMfzgr9cNOzMzaAWsFcJutBPa/gzZvthm0uLLMGBSboERjYbtxGwXXWz5MLRa+HAJGBsVf9AUrEFwbaBhOMPkj7YHm1t7HXLi34Zvh5MCGkOQbz5NMLk92+lyD8qWawgCrKGNkdQf5lcccp5IERGKYkY2Qq82qcvhzPJAKtsqH8i4lQ6nw1ka3WUNXEb2aFMFuyqHgsesqGin/28EyloCERPBsj0QIbDCqo0eOoG/ki4CWW1EPEbSoqBrepCf8H/jihghp73KolxgDfohORgrtQk51x5SSnRgm9c1JQM4BjJPHMEiV1nb1DqR8NjcG7dn5f3JZcnCtZtc05xk/EwFDq'

illegal_splitter_configuration2 = '0eNqV0+FqwyAQB/B3uc+mRJs2i68yRknaowiJEb2OheC7zySjFHod9aNGf/nfyc3Q9Td03lgCPYM5jzaA/pwhmKtt+2WPJoegwRAOIMC2w7Ii39rgRk9Fhz1BFGDsBX9Ay/glAC0ZMrhJ62I62dvQoU8HXhkC3BjStdEuf01UKWACXagYxZOichXJKfu3FflPlipXYbMcMitikePbSLFlKdPLXYzH8/ZJMWada7LJPu5KcL0hSnvPhe0Of6EYoMnsMptClpldZh9cytyW8IzKLCkpabjWQdQPcyvgG31YD9f7UjaVqupjE+Mv0RRKZg=='

legal_splitter_config = '0eNqVk2GLgzAMhv9LPtdhnZtn/8oxhm7hKGgsbXZMpP991eNgbD3PfkxJnrx5k07Qdjc0VhODmkBfBnKgPidw+ouabn7j0SAo0Iw9CKCmnyO2DTkzWM5a7Bi8AE1XvIOSXvxb7EynmdE+lRX+JACJNWv8EbAE45lufRsylfyrtQAzuFA20NwvoHIBI6is8LOSF0qxmZLJFcw+GSNjmPLdkfdpdocVwmGzkLVxjqnjRLVUiRuKQj42WJL9epLHCHWiJVEZMk+kBCnhgJczV09fSsA3WrckV/tc1mVRVsfa+wcvASep'

illegal_splitter_config3 = '0eNqVlNGKgzAQRf9lnmMxMa1rfqUsi7bDEtAoyXRZkfx7o6VQtllMniRm5uRec50Fuv6Gk9WGQC2gL6NxoM4LOP1t2n59R/OEoEATDsDAtMO6ItsaN42Wig57As9Amyv+guKe7Ta7qddEaF/ahP9kgIY0aXwI2Bbzl7kNXahU/L+jGUyjC22jWc8LqCKUzuFRBfpVW7w89sQq7A9UJEPLKFNGmFUuU+wzZbZ54SOYYzKGJ0s75TITPmGdbZfH7H68B+79Dg7HJ2FXVpMrq4yp4mWGrDgh+1+IpoHnpj9OqRLsFE8/0XviMjNDcSG56Q5awszZJpN6mYIMftC6rbiuSt5IIetT4/0d5ae3gw=='

print_2d = True

try:
    illegal_balancer = Balancer(illegal, print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    legal_balancer = Balancer(legal, print2d=print_2d, textures=TEXTURES)
    assert not legal_balancer.has_sideloads
except (IllegalConfigurations, IllegalEntities, AssertionError) as e:
    print(repr(e))
else:
    print("No Exceptions")


try:
    balancer2 = Balancer(string2, print2d=print_2d, textures=TEXTURES)
    assert not balancer2.has_sideloads
except (IllegalConfigurations, IllegalEntities, AssertionError) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    lane_balancer = Balancer(lane, print2d=print_2d, textures=TEXTURES)
    assert lane_balancer.has_sideloads
except (IllegalConfigurations, IllegalEntities, AssertionError) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_belt_configuration_balancer = Balancer(
        illegal_belt_configuration,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_underground_configuration_balancer = Balancer(
        illegal_underground_configuration,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_underground_configuration_balancer2 = Balancer(
        illegal_underground_configuration2,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_splitter_balancer = Balancer(
        illegal_splitter_configuration,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_splitter_balancer2 = Balancer(
        illegal_splitter_configuration2,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    legal_splitter_balancer = Balancer(
        legal_splitter_config,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")

try:
    illegal_splitter_balancer3 = Balancer(
        illegal_splitter_config3,
        print2d=print_2d, textures=TEXTURES)
except (IllegalConfigurations, IllegalEntities) as e:
    print(repr(e))
else:
    print("No Exceptions")
