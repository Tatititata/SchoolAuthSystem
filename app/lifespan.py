from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, inspect
from models import Base, Role, Permission, RolePermission, Class, ClassSubject, Subject
from models import User, UserRole, TeacherClassSubject, ParentStudent, Grade
from .database import engine
from .auth import hash_password


@asynccontextmanager
async def lifespan(app):
    print("Запуск сервера")

    async with AsyncSession(engine) as session:  

        conn = await session.connection()
        has_table = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table("users"))
        if not has_table:
            
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            await fill_tables(session)

    print("База данных готова к работе")
    
    yield  
    
    print("Выключение сервера")


async def fill_tables(session: AsyncSession) -> None:

        # Роли
        roles = await seed_roles(session)

        # Разрешения
        perms = await seed_permissions(session)

        # разрешения по ролям

        # admin - всё
        role_id=roles["admin"].id
        for perm in perms.values():
            session.add(RolePermission(role_id=role_id, permission_id=perm.id))

        base_perms = ["user:read", "profile:read", "profile:write", "schedule:read", "menu:read"]

        # director - всё на чтение + schedule:write
        director_perms = base_perms + ["gradebook:read", "schedule:write", "inventory:read"]
        
        # teacher - gradebook:read/write/delete
        teacher_perms = base_perms + ["gradebook:read", "gradebook:write", "gradebook:delete", "inventory:read"]

        # parent - gradebook:read (только своего ребёнка), schedule:read
        parent_perms = base_perms + ["gradebook:read"]

        # student - gradebook:read (только свои), schedule:read
        student_perms = base_perms + ["gradebook:read"]
        
        # caretaker - inventory:write
        caretaker_perms = base_perms + ["inventory:read", "inventory:write"]
        
        # cook - menu:write
        cook_perms = base_perms + ["menu:write", "inventory:read"]

        await grant_permissions(session, roles["director"].id, perms, director_perms)
        await grant_permissions(session, roles["teacher"].id, perms, teacher_perms)
        await grant_permissions(session, roles["parent"].id, perms, parent_perms)
        await grant_permissions(session, roles["student"].id, perms, student_perms)
        await grant_permissions(session, roles["caretaker"].id, perms, caretaker_perms)
        await grant_permissions(session, roles["cook"].id, perms, cook_perms)
        

        # тестовые классы
        class_5a = Class(name="5А", year=2025)
        class_5b = Class(name="5Б", year=2025)
        class_6a = Class(name="6А", year=2025)
        session.add_all([class_5a, class_5b, class_6a])
           
        # предметы
        math = Subject(name="Математика", description="Математика")
        russian = Subject(name="Русский язык", description="Русский язык")
        physics = Subject(name="Физика", description="Физика")
        session.add_all([math, russian, physics])
        await session.flush()
        
        # (class_subjects)
        cs_5a_math = ClassSubject(class_id=class_5a.id, subject_id=math.id)
        cs_5a_russian = ClassSubject(class_id=class_5a.id, subject_id=russian.id)
        cs_5b_math = ClassSubject(class_id=class_5b.id, subject_id=math.id)
        cs_6a_math = ClassSubject(class_id=class_6a.id, subject_id=math.id)
        cs_6a_physics = ClassSubject(class_id=class_6a.id, subject_id=physics.id)
        session.add_all([cs_5a_math, cs_5a_russian, cs_5b_math, cs_6a_math, cs_6a_physics])
        await session.flush()
        
        # тестовые пользователи
        teacher_math = User(email="t_math@sch.com", password_hash=hash_password("pass"),
            full_name="Иван Петрович", is_active=True)
        student_1 = User(email="s1@sch.com", password_hash=hash_password("pass"),
            full_name="Alice Test", is_active=True, class_id=class_5a.id)
        student_2 = User(email="s2@sch.com", password_hash=hash_password("pass"),
            full_name="Bob Test", is_active=True, class_id=class_6a.id)
        parent = User(email="p@sch.com", password_hash=hash_password("pass"),
            full_name="Maria Parenting", is_active=True)
        admin_user = User(email="a@sch.com", password_hash=hash_password("admin123"),
            full_name="Sys Admin", is_active=True)
        director = User(email="d@sch.com", password_hash=hash_password("pass"),
            full_name="Boss Director", is_active=True)
        caretaker = User(email="care@sch.com", password_hash=hash_password("pass"),
            full_name="Dick Care", is_active=True)
        cook = User(email="cook@sch.com", password_hash=hash_password("pass"),
            full_name="Kate Cook", is_active=True)
        session.add_all([teacher_math, student_1, student_2, parent, admin_user, director, caretaker, cook])
        await session.flush()

        session.add(TeacherClassSubject(teacher_id=teacher_math.id, class_subject_id=cs_5a_math.id))
        session.add(TeacherClassSubject(teacher_id=teacher_math.id, class_subject_id=cs_5b_math.id))
        session.add(TeacherClassSubject(teacher_id=teacher_math.id, class_subject_id=cs_6a_math.id))

        session.add(UserRole(user_id=student_1.id, role_id=roles["student"].id))
        session.add(UserRole(user_id=student_2.id, role_id=roles["student"].id))
        session.add(UserRole(user_id=parent.id, role_id=roles["parent"].id))
        session.add(UserRole(user_id=admin_user.id, role_id=roles["admin"].id))
        session.add(UserRole(user_id=teacher_math.id, role_id=roles["teacher"].id))
        session.add(UserRole(user_id=director.id, role_id=roles["director"].id))
        session.add(UserRole(user_id=caretaker.id, role_id=roles["caretaker"].id))
        session.add(UserRole(user_id=cook.id, role_id=roles["cook"].id))

        session.add(ParentStudent(parent_id=parent.id, student_id=student_1.id))
        session.add(ParentStudent(parent_id=parent.id, student_id=student_2.id))

        await session.flush()
        
        # оценки (grades)
        grade1 = Grade(
            student_id=student_1.id,
            class_subject_id=cs_5a_math.id,
            grade=5,
            teacher_id=teacher_math.id,
            comment = 'homework'
        )
        grade2 = Grade(
            student_id=student_1.id,
            class_subject_id=cs_5a_russian.id,
            grade=4,
            teacher_id=teacher_math.id,  
            comment = 'homework'
        )
        grade3 = Grade(
            student_id=student_2.id,
            class_subject_id=cs_6a_math.id,
            grade=3,
            teacher_id=teacher_math.id,
            comment = 'homework'
        )
        session.add_all([grade1, grade2, grade3])
        await session.commit()

async def seed_roles(session: AsyncSession) -> dict:
    roles = (await session.execute(select(Role))).scalars().all()
    roles = {role.name: role for role in roles}
    if roles:
        return roles
    roles_data = [
        ("admin", "System administrator"),
        ("director", "School director"),
        ("teacher", "Teacher"),
        ("parent", "Parent"),
        ("student", "Student"),
        ("caretaker", "Caretaker (завхоз)"),
        ("cook", "Cook (повар)"),
    ]
    for name, desc in roles_data:
        role = Role(name=name, description=desc)
        session.add(role)
        roles[name] = role
    await session.flush()
    return roles

async def seed_permissions(session: AsyncSession) -> dict:

    perms = (await session.execute(select(Permission))).scalars().all()
    perms = {f"{p.resource_type}:{p.action}": p for p in perms}
    if perms:
        return perms
    permissions_data = [
    # Ресурс: user
    ("user", "read"), ("user", "read_all"), ("user", "write"), ("user", "delete"),
    # Ресурс: profile
    ("profile", "read"), ("profile", "write"),
    # Ресурс: gradebook (журнал)
    ("gradebook", "read"), ("gradebook", "write"), ("gradebook", "delete"),
    # Ресурс: schedule (расписание)
    ("schedule", "read"), ("schedule", "write"),
    # Ресурс: menu (меню)
    ("menu", "read"), ("menu", "write"),
    # Ресурс: inventory (инвентарь)
    ("inventory", "read"), ("inventory", "write"),
    ]
    for resource, action in permissions_data:
        perm = Permission(resource_type=resource, action=action)
        session.add(perm)
        perms[f"{resource}:{action}"] = perm
    await session.flush()
    return perms

async def grant_permissions(session: AsyncSession, role_id: int, perms_dict: dict, perms_list: list) -> None:
    for perm_key in perms_list:
        if perm_key in perms_dict:
            session.add(RolePermission(role_id=role_id, permission_id=perms_dict[perm_key].id))
