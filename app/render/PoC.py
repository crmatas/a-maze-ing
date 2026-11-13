
from mlx import Mlx


# Define el callback (función que se ejecuta en respuesta a un evento)
# del mouse
def mymouse(button, x, y, mystuff):
    print(f"Got mouse event! button {button} at {x},{y}.")


# Define el callback del teclado
def mykey(keynum, mystuff):
    print(f"Got key {keynum}, and got my stuff back:")
    print(mystuff)
    # Si se presiona la barra espaciadora (keynum 32),
    # desactiva el hook del mouse.
    if keynum == 32:
        m.mlx_mouse_hook(win_ptr, None, None)
    elif keynum == 27:
        m.mlx_loop_exit(mlx_ptr)
    elif keynum == 113:  # Q key
        m.mlx_mouse_hook(win_ptr, mymouse, None)
    elif keynum == 119:  # W key
        m.mlx_mouse_hide(mlx_ptr)
    elif keynum == 101:  # E key
        m.mlx_mouse_show(mlx_ptr)
    elif keynum in (65361, 65362, 65363, 65364):
        dx, dy = {
            65361: (-10, 0),
            65362: (0, -10),
            65363: (10, 0),
            65364: (0, 10),
        }[keynum]
        _, x, y = m.mlx_mouse_get_pos(win_ptr)
        move_result = m.mlx_mouse_move(win_ptr, x + dx, y + dy)
        m.mlx_do_sync(mlx_ptr)
        _, actual_x, actual_y = m.mlx_mouse_get_pos(win_ptr)
        print(f"move={move_result}, actual={actual_x},{actual_y}")


# Define el callback de cierre de ventana
def gere_close(dummy):
    m.mlx_loop_exit(mlx_ptr)


# Instancia la clase
m = Mlx()
# Inicializa la clase
mlx_ptr = m.mlx_init()
# Crea una nueva ventana
win_ptr = m.mlx_new_window(mlx_ptr, 200, 200, "win title")
# Limpia la ventana
m.mlx_clear_window(mlx_ptr, win_ptr)
# Escribe un texto en la ventana
m.mlx_string_put(mlx_ptr, win_ptr, 20, 20, 255, "Hello PyMlx!")
# Obtiene el tamaño de la pantalla
(ret, w, h) = m.mlx_get_screen_size(mlx_ptr)
print(f"Got screen size: {w} x {h} .")

stuff = [1, 2]
# Prepara los datos que se pasarán a los hooks
# Un hook es una función que se ejecuta en respuesta a un evento específico.
# Ejemplo: Un clic del mouse o una pulsación de tecla.
m.mlx_mouse_hook(win_ptr, mymouse, None)

# Configura los hooks para el mouse y el teclado
m.mlx_key_hook(win_ptr, mykey, stuff)
# Configura el hook para cerrar la ventana
m.mlx_hook(win_ptr, 33, 0, gere_close, None)

m.mlx_loop(mlx_ptr)
