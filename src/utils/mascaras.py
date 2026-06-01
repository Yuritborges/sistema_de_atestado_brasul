"""

Máscaras de entrada (data DD/MM/AAAA).

"""





def formatar_data_entry(entry) -> None:

    """Aplica máscara DD/MM/AAAA no conteúdo atual do campo."""

    raw = "".join(c for c in entry.get() if c.isdigit())[:8]

    partes = []

    if len(raw) >= 2:

        partes.append(raw[:2])

        if len(raw) >= 4:

            partes.append(raw[2:4])

            if len(raw) > 4:

                partes.append(raw[4:8])

        elif len(raw) > 2:

            partes.append(raw[2:])

    else:

        partes.append(raw)



    novo = "/".join(p for p in partes if p != "")

    entry.delete(0, "end")

    entry.insert(0, novo)





def vincular_data(entry):

    """Insere barras automaticamente enquanto o usuário digita."""



    def _formatar(_event=None):

        formatar_data_entry(entry)



    entry.bind("<KeyRelease>", _formatar)


