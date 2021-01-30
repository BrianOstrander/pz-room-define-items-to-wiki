import sys
from pathlib import Path
from lupa import LuaRuntime
from distribution import Distribution
from room_descriptions import ROOM_DESCRIPTIONS
from version import VERSION

DISTRIBUTIONS_PATH = 'resources/Distributions.lua'
PROCEDURAL_DISTRIBUTIONS_PATH = 'resources/ProceduralDistributions.lua'
EXPORTS_PATH = 'exports'
EXPORTS_WARNING_PATH = 'exports/DO NOT SAVE HERE.txt'
EXPORTS_FILE_PATH = 'exports/wiki_result.txt'

def main():
    root_path = Path(sys.path[0])
    distributions_path = root_path.joinpath(DISTRIBUTIONS_PATH)
    procedural_distributions_path = root_path.joinpath(PROCEDURAL_DISTRIBUTIONS_PATH)

    if not distributions_path.exists():
        print('Unable to find ' + DISTRIBUTIONS_PATH)
        return

    if not procedural_distributions_path.exists():
        print('Unable to find ' + PROCEDURAL_DISTRIBUTIONS_PATH)
        return

    exports_path = root_path.joinpath(EXPORTS_PATH)

    if not exports_path.exists():
        exports_path.mkdir()

    exports_warning_path = root_path.joinpath(EXPORTS_WARNING_PATH)

    if not exports_warning_path.exists():
        with open(exports_warning_path, "w") as warning_file:
            print('Do not save any changes to this directory, it will be overwritten by the next operation!', file=warning_file)

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(distributions_path, "r").read())
    lua.execute(open(procedural_distributions_path, "r").read())
    distribution_lua = lua.globals().Distributions
    distribution_procedural_lua = lua.globals().ProceduralDistributions.list

    procedural_distribution_entries = []

    for node in distribution_procedural_lua.items():
        procedural_distribution_entries.append(Distribution(node, True, []))

    distribution_entries = []

    for node in distribution_lua[1].items():
        distribution_entries.append(Distribution(node, False, procedural_distribution_entries))

    export_result = '\'\'\'Warning: Everything below has been programmatically generated - any changes made will be ' \
                    'lost on the next update!\'\'\' '

    export_result = export_result + '\n\n\'\'\'Generated from Project Zomboid version {} - Using room-define-to-items ' \
                                    'version {}\'\'\''.format(VERSION['PZ'], VERSION['PROJECT'])

    export_result = export_result + '\n\nIf you would like to modify how this information is presented, submit a ' \
                                    'merge request or create an issue [' \
                                    'https://github.com/BrianOstrander/pz-room-define-items-to-wiki here.] '

    export_result = export_result + '\n\nAll room defines are presented as is, for use in your custom maps. Exact ' \
                                    'item names have been modified for increased readability and a greater chance of ' \
                                    'linking to their respective wiki articles. For a full list of these items refer ' \
                                    'to the \'\'Distributions.lua\'\' and \'\'ProceduralDistributions.lua\'\' files ' \
                                    'in your Project Zomboid install directory. '

    export_result = export_result + '\n\n== Room Defines and Item Spawns =='

    for entry in sorted(distribution_entries, key=lambda e: e.name.lower()):
        if entry.type == Distribution.TYPE_ROOM:
            export_result = export_result + '\n==={}==='.format(entry.name)
            description = ROOM_DESCRIPTIONS.get(entry.name)
            if description:
                export_result = '\n' + export_result + description

            export_result = export_result + '\n{| class="wikitable sortable"'
            export_result = export_result + '\n|-'
            # header = '! Header text !! Header text !! Header text'
            export_result = export_result + '\n! Container !! Items'

            containers = sorted(entry.containers)
            items = []
            for key, item in entry.items.items():
                items.append(item)
            items = sorted(items, key=lambda i: i.id)

            for container in containers:
                result = '| [[{}]] || '.format(container)
                any_appended = False
                for item in items:
                    if container in item.containers:
                        result = '{}[[{}]], '.format(result, item.id)
                        any_appended = True
                if any_appended:
                    export_result = export_result + '\n|-'
                    export_result = export_result + '\n' + result[:-2]

            export_result = export_result + '\n|}'

    exports_file_path = root_path.joinpath(EXPORTS_FILE_PATH)
    if exports_file_path.exists():
        exports_file_path.unlink()

    with open(exports_file_path, "w") as exports_file:
        print(export_result, file=exports_file)

    print('Check {} for the results of this operation.'.format(exports_file_path))

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
