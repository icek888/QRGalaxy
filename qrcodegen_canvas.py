from qrcodegen import QrCode
from PIL import Image, ImageDraw


def generate_qr_with_canvas(
    url,
    path,
    style="square",
    fill_color="#000000",
    back_color="#ffffff",
    eye_frame_color="#000000",
    eye_ball_color="#000000",
    logo_file=None,
):
    # Генерация базового QR-кода
    qr = QrCode.encode_text(url, QrCode.Ecc.H)
    size = qr.get_size()
    scale = 10
    border = 4
    img_size = (size + border * 2) * scale

    img = Image.new("RGB", (img_size, img_size), back_color)
    draw = ImageDraw.Draw(img)

    # Основной рисунок
    for y in range(size):
        for x in range(size):
            if qr.get_module(x, y):
                px = (x + border) * scale
                py = (y + border) * scale
                draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=fill_color)

    # Отрисовка глаз отдельно
    def draw_eye(cx, cy):
        ex = (cx + border) * scale
        ey = (cy + border) * scale
        draw.rectangle([ex, ey, ex + scale * 7 - 1, ey + scale * 7 - 1], fill=eye_frame_color)
        draw.rectangle([
            ex + scale * 2,
            ey + scale * 2,
            ex + scale * 5 - 1,
            ey + scale * 5 - 1
        ], fill=eye_ball_color)

    draw_eye(0, 0)
    draw_eye(size - 7, 0)
    draw_eye(0, size - 7)

    # Вставка логотипа
    if logo_file:
        logo = Image.open(logo_file).convert("RGBA")
        logo_size = img_size // 4
        logo = logo.resize((logo_size, logo_size))

        logo_with_border = Image.new("RGBA", (logo_size + 10, logo_size + 10), back_color)
        logo_with_border.paste(logo, (5, 5), logo)

        lx = (img.size[0] - logo_with_border.size[0]) // 2
        ly = (img.size[1] - logo_with_border.size[1]) // 2
        img.paste(logo_with_border, (lx, ly), logo_with_border)

    img.save(path)
