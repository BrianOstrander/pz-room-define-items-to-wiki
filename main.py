import sys
from pathlib import Path
import lupa
from lupa import LuaRuntime
from distribution import Distribution

DISTRIBUTIONS_PATH = 'resources/Distributions.lua'
PROCEDURAL_DISTRIBUTIONS_PATH = 'resources/ProceduralDistributions.lua'

ROOM_DESCRIPTIONS = {
    'some room name': 'some description'
}

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

    for entry in sorted(distribution_entries, key=lambda e: e.name.lower()):
        if entry.type == Distribution.TYPE_ROOM:
            print('==={}==='.format(entry.name))
            description = ROOM_DESCRIPTIONS.get(entry.name)
            if description:
                print(description)

            print('{| class="wikitable sortable"')
            print('|-')
            # header = '! Header text !! Header text !! Header text'
            print('! Container !! Items')

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
                    print('|-')
                    print(result[:-2])

            print('|}')


    return

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
