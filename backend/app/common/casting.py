import hashlib
import re


NONCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


def validate_cast_nonce(value):
    if not isinstance(value, str) or not NONCE_PATTERN.match(value):
        raise ValueError("cast_nonce must contain 16 to 128 ASCII letters, digits, underscore, or hyphen")
    return value


def nonce_hash(value):
    nonce = validate_cast_nonce(value)
    return "sha256:" + hashlib.sha256(nonce.encode("ascii")).hexdigest()


def derive_integer(domain, nonce, sequence, minimum, maximum):
    if minimum > maximum:
        raise ValueError("minimum cannot exceed maximum")
    value = validate_cast_nonce(nonce)
    material = "{}\0{}\0{}".format(domain, value, int(sequence)).encode("ascii")
    raw = int.from_bytes(hashlib.sha256(material).digest(), "big")
    return minimum + raw % (maximum - minimum + 1)


def derive_coin_lines(domain, nonce):
    rounds = []
    line_values = []
    for line in range(1, 7):
        coins = [derive_integer(domain, nonce, (line - 1) * 3 + coin, 2, 3) for coin in range(1, 4)]
        value = sum(coins)
        rounds.append({"line": line, "coins": coins, "value": value})
        line_values.append(value)
    return line_values, rounds
