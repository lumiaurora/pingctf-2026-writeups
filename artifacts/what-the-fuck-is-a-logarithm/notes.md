# What the fuck is a logarithm

- Category: rev
- Language: Python
- Observed flag length: 32 characters
- Flag format hint: `ping{.*}`

## Useful constants

- Base: `73.21`
- Alphabet used by the solver: `_0123456789abcdefghijklmnopqrstuvwxyz{}`

## Chunk targets

The generated checker reduces to four weighted sums over 8-character chunks:

```text
46741716782375706.8396419575653316
46291277424349185.5548286712719316
42149201139278358.4223548171552311
64147886106222656.2384332732886897
```

Each chunk is evaluated as:

```python
sum((ord(ch) - 48) * Decimal("73.21") ** i for i, ch in enumerate(chunk, 1))
```

## Recovered chunks

```text
ping{1_h
473_m47h
___17_5c
4r35_me}
```

## Final flag

```text
ping{1_h473_m47h___17_5c4r35_me}
```
