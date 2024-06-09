import brci
from PIL import Image
import os

cwd = os.path.dirname(os.path.realpath(__file__))
brci.br_property_types['Font'] = 'str8'


def open_image(file_path):
    return Image.open(file_path)


def resize_image(image, img_size_x, img_size_y):
    return image.resize((img_size_x, img_size_y))


def quantize_colors(image, num_colors):
    return image.quantize(colors=num_colors)


def convert_to_hsv(image):
    # First, convert the image to RGB if it's not already in that format
    rgb_image = image.convert("RGB")

    # Then, convert the RGB image to HSV
    hsv_image = rgb_image.convert("HSV")
    return hsv_image


def write_to_brick_rigs_text(image: Image, name: str, image_size: float):

    data = brci.BRCI()

    data.project_folder_directory = cwd
    data.project_name = 'br_' + name

    true_str: str = '||||'
    false_str: str = '   '

    pixels = image.load()

    color_map: dict[tuple, dict[int, str]] = {}

    # len(y) = the amount of colors (why?)

    # Create all colors and assign them ligns where they're found
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            color = pixels[x, y]
            if color not in color_map.keys():
                color_map[color] = {}
            if y not in color_map[color].keys():
                color_map[color][y] = ''

    # Add true_str/false_str to all ligns
    for y in range(image.size[1]):
        for x in range(image.size[0]):
            pixel_color = image.getpixel((x, y))
            pixel_color = (
                pixel_color[0],
                int((pixel_color[1]/255)**0.3 * 255),
                pixel_color[2]
            )
            image.setpixel((x, y), pixel_color)

            for color in color_map:
                if y in color_map[color].keys():
                    if color == pixel_color:
                        color_map[color][y] += true_str
                    else:
                        color_map[color][y] += false_str


    # Building all that
    for color in color_map.keys():

        y_pos: float = 0.0

        for y in color_map[color].keys():

            data.anb(f'text_{color}_{y}', 'TextBrick', {
                'Font': 'Orbitron',
                'FontSize': image_size,
                'Text': color_map[color][y],
                'TextColor': list(color)
            }, [0, y_pos, 0], [0, 0, 0])

            data.anb(f'text_{color}_{y}', 'TextBrick', {
                'Font': 'Orbitron',
                'FontSize': image_size,
                'Text': color_map[color][y],
                'TextColor': list(color)
            }, [-0.0835*image_size, y_pos, 0], [0, 0, 0])

            y_pos += -0.71*image_size

    data.write_brv()
    data.write_metadata()
    data.write_preview()
    data.write_to_br()


def compress_grid(grid):
    compressed_list = []
    rows = len(grid)
    cols = len(grid[0])

    for i in range(rows):
        for j in range(cols):
            if grid[i][j]:
                value = grid[i][j]
                size_x = 1
                size_y = 1
                while j + size_x < cols and grid[i][j + size_x] == value:
                    size_x += 1
                while i + size_y < rows:
                    valid = all(grid[i + size_y][j + k] == value for k in range(size_x))
                    if valid:
                        size_y += 1
                    else:
                        break
                compressed_list.append((value, j, i, size_x, size_y))

                for x in range(i, i + size_y):
                    for y in range(j, j + size_x):
                        grid[x][y] = False
    return compressed_list



def write_to_brick_rigs_scalables(image: Image, name: str, pixel_size: float, thickness: float):

    # Putting it in a list
    hsv_values: list[list[list[int, int, int]]] = []
    for y in range(image.height):
        row = []
        for x in range(image.width):
            pixel = image.getpixel((x, y))
            adjusted_hue = pixel[0]
            adjusted_sat = int((pixel[1]/255)**0.3 * 255)
            adjusted_val = int((pixel[2]/255)**1.6666 * 255)
            row.append((adjusted_hue, adjusted_sat, adjusted_val))
        hsv_values.append(row)

    # Optimizing
    # Value, X, Y, Width, Height
    grid_chunks: list[list[list[int, int, int], int, int, int, int]] = compress_grid(hsv_values)

    data = brci.BRCI()
    data.project_folder_directory = cwd
    data.project_name = data.project_display_name = name
    data.project_description = 'Generated using BrickImg A1'

    for chunk in grid_chunks:

        brick_size: list[float] = [
            pixel_size * chunk[3] * 0.1,
            pixel_size * chunk[4] * 0.1,
            thickness * 0.1
        ]

        brick_pos: list[float] = [
            - (chunk[1] + chunk[3] / 2) * pixel_size,
            - (chunk[2] + chunk[4] / 2) * pixel_size,
            10
        ]

        data.anb(f'brick_{chunk}', 'ScalableBrick', {
            'BrickColor': [*chunk[0], 255],
            'BrickSize': brick_size
        }, brick_pos, [0, 0, 0])

    data.write_brv()
    data.write_metadata()
    data.write_preview()
    data.write_to_br()




def main():

    name = input("Enter image name (Extension included)\n> ")
    file_path = os.path.join(cwd, name)

    image = open_image(file_path)

    img_size_y = int(input("Enter image height (pixels)\n> "))
    img_size_x = input("Enter image width (pixels) (leave empty to automatically calculate)\n> ")

    if img_size_x == '':
        img_size_x = int(image.size[0] * (img_size_y / image.size[1]))
    else:
        img_size_x = int(img_size_x)
    num_colors = int(input("Enter number of different colors\n> "))

    resized_image = resize_image(image, img_size_x, img_size_y)
    quantized_image = quantize_colors(resized_image, num_colors)
    hsl_image = convert_to_hsv(quantized_image)

    pixel_size: float = float(input("Enter pixel size (centimeters)\n> "))
    size_z: float = float(input("Enter image thickness (centimeters)\n> "))
    write_to_brick_rigs_scalables(hsl_image, 'br_' + name.split('.')[0], pixel_size, size_z)

    # hsl_image.show()


if __name__ == "__main__":
    main()