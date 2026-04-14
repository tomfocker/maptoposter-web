def build_save_kwargs(output_format: str, dpi: int, facecolor: str = "#FFFFFF") -> dict:
    fmt = output_format.lower()
    save_kwargs = {
        "facecolor": facecolor,
    }

    if fmt == "png":
        save_kwargs["dpi"] = dpi

    return save_kwargs
