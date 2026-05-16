from decimal import Decimal
from datetime import datetime

from app import create_app
from app.extensions import db, appbuilder
from app.models import Categoria, Producto, Cliente, Pedido, PedidoItem


app = create_app()


def get_or_create(model, defaults=None, **kwargs):
    obj = db.session.query(model).filter_by(**kwargs).first()
    if obj:
        return obj

    data = dict(kwargs)
    if defaults:
        data.update(defaults)

    obj = model(**data)
    db.session.add(obj)
    db.session.commit()
    return obj


def crear_roles_y_usuarios():
    sm = appbuilder.sm

    # Crear roles
    rol_cajero = sm.find_role("Cajero") or sm.add_role("Cajero")
    rol_mesero = sm.find_role("Mesero") or sm.add_role("Mesero")
    rol_reportes = sm.find_role("Reportes") or sm.add_role("Reportes")

    db.session.commit()

    def agregar_permiso(role, permission_name, view_menu_name):
        permiso = sm.find_permission_view_menu(permission_name, view_menu_name)
        if permiso and permiso not in role.permissions:
            role.permissions.append(permiso)

    # Permisos Cajero
    for vista in [
        "CategoriaModelView",
        "ProductoModelView",
        "ClienteModelView",
        "PedidoModelView",
        "PedidoItemModelView",
    ]:
        agregar_permiso(rol_cajero, "can list", vista)
        agregar_permiso(rol_cajero, "can show", vista)
        agregar_permiso(rol_cajero, "can add", vista)
        agregar_permiso(rol_cajero, "can edit", vista)

    # Permisos Mesero
    for vista in [
        "CategoriaModelView",
        "ProductoModelView",
        "PedidoModelView",
        "PedidoItemModelView",
    ]:
        agregar_permiso(rol_mesero, "can list", vista)
        agregar_permiso(rol_mesero, "can show", vista)

    agregar_permiso(rol_mesero, "can add", "PedidoModelView")
    agregar_permiso(rol_mesero, "can add", "PedidoItemModelView")

    # Permisos Reportes
    for vista in [
        "ReporteView",
        "GraficasView",
    ]:
        agregar_permiso(rol_reportes, "can index", vista)

    # Permisos básicos para que puedan entrar al sistema
    for rol in [rol_cajero, rol_mesero, rol_reportes]:
        agregar_permiso(rol, "can index", "IndexView")
        agregar_permiso(rol, "can this form get", "UserInfoEditView")
        agregar_permiso(rol, "can this form post", "UserInfoEditView")
        agregar_permiso(rol, "can this form get", "ResetMyPasswordView")
        agregar_permiso(rol, "can this form post", "ResetMyPasswordView")

    db.session.commit()

    # Crear usuarios
    if not sm.find_user(username="cajero"):
        sm.add_user(
            username="cajero",
            first_name="Cajero",
            last_name="Dolci",
            email="cajero@dolcimomenti.com",
            role=rol_cajero,
            password="cajero123"
        )

    if not sm.find_user(username="mesero"):
        sm.add_user(
            username="mesero",
            first_name="Mesero",
            last_name="Dolci",
            email="mesero@dolcimomenti.com",
            role=rol_mesero,
            password="mesero123"
        )

    if not sm.find_user(username="reportes"):
        sm.add_user(
            username="reportes",
            first_name="Usuario",
            last_name="Reportes",
            email="reportes@dolcimomenti.com",
            role=rol_reportes,
            password="reportes123"
        )

    db.session.commit()


def crear_datos_demo():
    # Categorías
    helados = get_or_create(
        Categoria,
        nombre="Helados",
        defaults={
            "descripcion": "Helados artesanales de diferentes sabores.",
            "activa": True
        }
    )

    cafes = get_or_create(
        Categoria,
        nombre="Cafés",
        defaults={
            "descripcion": "Bebidas calientes y frías a base de café.",
            "activa": True
        }
    )

    postres = get_or_create(
        Categoria,
        nombre="Postres",
        defaults={
            "descripcion": "Postres dulces para acompañar pedidos.",
            "activa": True
        }
    )

    bebidas = get_or_create(
        Categoria,
        nombre="Bebidas",
        defaults={
            "descripcion": "Bebidas frías para cafetería.",
            "activa": True
        }
    )

    # Productos
    productos = {
        "Helado de chocolate": get_or_create(
            Producto,
            nombre="Helado de chocolate",
            defaults={
                "descripcion": "Helado artesanal sabor chocolate.",
                "precio": Decimal("8.00"),
                "stock": 40,
                "categoria": helados,
                "estado": True
            }
        ),
        "Helado de frutilla": get_or_create(
            Producto,
            nombre="Helado de frutilla",
            defaults={
                "descripcion": "Helado artesanal sabor frutilla.",
                "precio": Decimal("8.00"),
                "stock": 35,
                "categoria": helados,
                "estado": True
            }
        ),
        "Capuchino": get_or_create(
            Producto,
            nombre="Capuchino",
            defaults={
                "descripcion": "Café capuchino caliente.",
                "precio": Decimal("12.00"),
                "stock": 50,
                "categoria": cafes,
                "estado": True
            }
        ),
        "Latte": get_or_create(
            Producto,
            nombre="Latte",
            defaults={
                "descripcion": "Café latte suave.",
                "precio": Decimal("13.00"),
                "stock": 45,
                "categoria": cafes,
                "estado": True
            }
        ),
        "Brownie": get_or_create(
            Producto,
            nombre="Brownie",
            defaults={
                "descripcion": "Brownie de chocolate.",
                "precio": Decimal("10.00"),
                "stock": 30,
                "categoria": postres,
                "estado": True
            }
        ),
        "Cheesecake": get_or_create(
            Producto,
            nombre="Cheesecake",
            defaults={
                "descripcion": "Porción de cheesecake.",
                "precio": Decimal("15.00"),
                "stock": 20,
                "categoria": postres,
                "estado": True
            }
        ),
        "Jugo de maracuyá": get_or_create(
            Producto,
            nombre="Jugo de maracuyá",
            defaults={
                "descripcion": "Jugo natural frío.",
                "precio": Decimal("9.00"),
                "stock": 25,
                "categoria": bebidas,
                "estado": True
            }
        ),
    }

    # Clientes
    clientes = [
        get_or_create(Cliente, nombre="Ana Vargas", defaults={"email": "ana@email.com", "telefono": "70000001", "direccion": "Zona Central"}),
        get_or_create(Cliente, nombre="Luis Mamani", defaults={"email": "luis@email.com", "telefono": "70000002", "direccion": "Av. América"}),
        get_or_create(Cliente, nombre="Carla Rojas", defaults={"email": "carla@email.com", "telefono": "70000003", "direccion": "Barrio Petrolero"}),
        get_or_create(Cliente, nombre="Pedro Flores", defaults={"email": "pedro@email.com", "telefono": "70000004", "direccion": "Zona Mercado"}),
        get_or_create(Cliente, nombre="María López", defaults={"email": "maria@email.com", "telefono": "70000005", "direccion": "Centro"}),
    ]

    pedidos_demo = [
        (clientes[0], "entregado", [("Helado de chocolate", 2), ("Capuchino", 1)]),
        (clientes[1], "pendiente", [("Latte", 2), ("Brownie", 1)]),
        (clientes[2], "entregado", [("Helado de frutilla", 3), ("Jugo de maracuyá", 2)]),
        (clientes[3], "cancelado", [("Cheesecake", 1)]),
        (clientes[4], "entregado", [("Capuchino", 2), ("Brownie", 2)]),
        (clientes[0], "pendiente", [("Helado de chocolate", 1), ("Latte", 1)]),
        (clientes[1], "entregado", [("Jugo de maracuyá", 3), ("Brownie", 1)]),
        (clientes[2], "entregado", [("Cheesecake", 2), ("Capuchino", 1)]),
        (clientes[3], "pendiente", [("Helado de frutilla", 2), ("Latte", 1)]),
        (clientes[4], "entregado", [("Helado de chocolate", 3), ("Brownie", 1), ("Capuchino", 1)]),
    ]

    # Para evitar duplicar pedidos si corres el script dos veces
    if db.session.query(Pedido).count() >= 10:
        print("Los pedidos demo ya existen. No se duplicaron.")
        return

    for cliente, estado, items in pedidos_demo:
        pedido = Pedido(
            cliente=cliente,
            estado=estado,
            total=Decimal("0.00"),
            creado_en=datetime.utcnow()
        )
        db.session.add(pedido)
        db.session.flush()

        total_pedido = Decimal("0.00")

        for nombre_producto, cantidad in items:
            producto = productos[nombre_producto]
            precio = Decimal(producto.precio)
            subtotal = precio * cantidad

            item = PedidoItem(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )

            db.session.add(item)
            total_pedido += subtotal

        pedido.total = total_pedido

        if estado == "entregado":
            pedido.entregado_en = datetime.utcnow()

    db.session.commit()


with app.app_context():
    crear_roles_y_usuarios()
    crear_datos_demo()
    print("Datos demo creados correctamente.")
    print("Usuarios creados:")
    print("admin: el que ya tienes creado")
    print("cajero / cajero123")
    print("mesero / mesero123")
    print("reportes / reportes123")