from exdreader import GameData, ParsedFileName, ExcelListFile


def main():
    path = 'C:\\Program Files (x86)\\SquareEnix\\FINAL FANTASY XIV - A Realm Reborn\\game\\'
    game_data = GameData(path)

    rootexl = ExcelListFile(game_data.get_file(ParsedFileName('exd/root.exl')))

    print(dict(sorted(rootexl.dict.items())))


main()
