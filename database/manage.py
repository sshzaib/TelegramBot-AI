def insert_user(firstname: str, lastname: str, username: str) -> None:
    query = user_table.insert().values(
        firstname=firstname, lastname=lastname, username=username
    )
    connection.execute(query)
