### mutante 1: precio_final(1000, 150) devuelve -500 porque la condición usa `and` y nunca se cumple, así que ningún descuento se rechaza.
```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct < 0 and descuento_pct > 100:
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return precio - (precio * descuento_pct) // 100
```

### mutante 2: precio_final(1000, -50) devuelve 1500 porque el rango se valida sobre el valor absoluto: se rechazan 150 y -150, pero no los negativos entre -100 y -1.
```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if abs(descuento_pct) > 100:
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return precio - (precio * descuento_pct) // 100
```

### mutante 3: precio_final(1000, 300) devuelve 2000 porque se rechazan los negativos pero el exceso sobre 100 % solo se "corrige" con abs() sobre el resultado, que supera el precio original.
```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct < 0:
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return abs(precio - (precio * descuento_pct) // 100)
```

### mutante 4: precio_final(1000, 199) devuelve -990 porque el rango se comprueba con división entera: se rechazan los negativos y los valores desde 200, pero 101..199 dan cociente 1 y pasan.
```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    if descuento_pct // 100 not in (0, 1):
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return precio - (precio * descuento_pct) // 100
```

### mutante 5: precio_final(200, -10) devuelve 220 porque se valida el resultado en vez de la entrada y solo se comprueba que no sea negativo: 150 se rechaza, pero un descuento negativo sube el precio.
```python
def precio_final(precio: int, descuento_pct: int) -> int:
    """Aplica un descuento porcentual a un precio en céntimos."""
    final = precio - (precio * descuento_pct) // 100
    if final < 0:
        raise ValueError("El descuento debe estar entre 0 y 100.")
    return final
```
