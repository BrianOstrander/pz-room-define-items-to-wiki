import string
import re
import lupa
from item import Item

class Distribution:

    NAME_ALL = 'all'
    KEY_SKIPS = [
        'rolls',
        'items',
        'noAutoAge',
        'dontSpawnAmmo',
        'procedural', # This never appears without also procList being present.
        # Ones below need more investigation...
        'procList',
        'fillRand',
        'junk'
    ]
    KEY_ITEMS = 'items'
    KEY_PROCEDURAL = 'procList'
    KEY_JUNK = 'junk'
    KEY_ALL = 'all'

    TYPE_ROOM = 'room'
    TYPE_CONTAINER = 'container'
    TYPE_PROCEDURAL = 'procedural'
    TYPE_META = 'meta'

    LUA_TYPE_TABLE = 'table'

    # Translates ids before anything else occurs, matching keys get replaced with their value. Anything captured by this
    # list will not go through any further filtering.
    ITEM_ID_PRE_TRANSLATION = {
        'Hat_Army': 'Army Hat',
        'CanoePadelX2': 'Canoe Padels'
    }

    # If any of these strings exist anywhere in a item's id, we do not strip numbers from it.
    # This prevents stripping certain ammo types.
    ITEM_ID_INTEGER_TRUNCATE_BLACKLIST_AGGRESSIVE = [
        'Bullets',
        'Box'
    ]

    # Remove any instances of the following from ids, the order is important!
    ITEM_ID_BLACKLIST = [
        'DOWN',
        'Bag_',
        'farming.',
        'camping.',
        'Radio.',
        'Base.',
        '_DefaultTEXTURE_TINT',
        '_DefaultTEXTURE_HUE',
        '_DefaultTEXTURE',
        '_DefaultDECAL_TINT',
        '_Short',
        '_Knees',
        '_Normal',
        '_Long',
        '_Ankle',
        'Hat_',
        '_TINT',
        'TINT',
        'TEXTURE',
        '_Full',
        'Full',
        '_Random',
        '_Pattern',
        '_Red',
        '_Green',
        '_Yellow',
        '_Blue',
        '_WhiteLongSleeve',
        '_White',
        '_Black',
        '_DiamondPattern'
    ]

    # If any of the following exists anywhere in a id, replace the entire id with the value.
    ITEM_ID_TRANSLATION_AGGRESSIVE = {
        'Gloves_Leather': 'Gloves Leather',
        'Map': 'Map',
        'Bracelet': 'Bracelet',
        'Earring': 'Earring',
        'NoseRing_': 'Nose Ring',
        'NoseStud_': 'Nose Stud',
        'Necklace': 'Necklace',
        'HairDye': 'Hair Dye',
        'BowTie': 'Bow Tie',
        'Ring_': 'Ring',
        'WristWatch_Right_Classic': 'Watch Classic',
        'WristWatch_Left_Classic': 'Watch Classic',
        'WristWatch_Right_Digital': 'Watch Digital',
        'WristWatch_Left_Digital': 'Watch Digital'
    }

    # After all previous steps, translate any matching ids to the following values.
    # If translation occurs, injection of whitespace will not occur!
    ITEM_ID_TRANSLATION = {
        'HandTorch': 'Flashlight',
        'Bullets38Box': '38 Box',
        'Bullets44Box': '44 Box',
        'Bullets45Box': '45 Box',
        'Bullets38': 'Bullets 38',
        'Bullets9mm': '9mm_Rounds|Bullets 9mm',
        'Bullets9mmBox': '9mm_Rounds|9mm Box',
        'LaCrosseStick': 'Lacrosse Stick',
        'SPHhelmet': 'SPH Helmet', # No idea what this actually is...
        'TVDinner': 'TV Dinner',
        'CDplayer': 'CD Player',
        'ALICEpack_Army': 'Large_Backpack|ALICE Pack - Army',
        'ALICEpack': 'Large_Backpack|ALICE Pack',
        'BookCarpentry': 'Skill_Books|Skill Book - Carpentry',
        'BookCooking': 'Skill_Books|Skill Book - Cooking',
        'BookElectrician': 'Skill_Books|Skill Book - Electrician',
        'BookFarming': 'Skill_Books|Skill Book - Farming',
        'BookFirstAid': 'Skill_Books|Skill Book - First Aid',
        'BookFishing': 'Skill_Books|Skill Book - Fishing',
        'BookForaging': 'Skill_Books|Skill Book - Foraging',
        'BookMechanic': 'Skill_Books|Skill Book - Mechanic',
        'BookMetalWelding': 'Skill_Books|Skill Book - Metalworking',
        'BookTailoring': 'Skill_Books|Skill Book - Tailoring',
        'BookTrapping': 'Skill_Books|Skill Book - Trapping',
        'CookingMag': 'Recipe_Magazines| Recipe Magazine - Cooking',
        'ElectronicsMag': 'Recipe_Magazines| Recipe Magazine - Electronics',
        'EngineerMag': 'Recipe_Magazines| Recipe Magazine - Engineering',
        'FarmingMag': 'Recipe_Magazines| Recipe Magazine - Farming',
        'FishingMag': 'Recipe_Magazines| Recipe Magazine - Fishing',
        'HerbalistMag': 'Recipe_Magazines| Recipe Magazine - Herbalist',
        'HuntingMag': 'Recipe_Magazines| Recipe Magazine - Hunting',
        'MechanicMag': 'Recipe_Magazines| Recipe Magazine - Mechanic',
        'MetalworkMag': 'Recipe_Magazines| Recipe Magazine - Metalworking',
        'RadioMag': 'Recipe_Magazines| Recipe Magazine - Radio',
        'NormalHikingBag': 'Normal Hiking Bag',
        'PillsAntiDep': 'Antidepressants',
        'PillsBeta': 'Beta Blockers',
        'PillsSleepingTablets': 'Sleeping Tablets',
        'PillsVitamins': 'Vitamins',
        'WhiskeyEmpty': 'Empty_Bottle_(Alcohol)|Whiskey Empty',
        'BeerEmpty': 'Empty_Bottle_(Alcohol)|Beer Empty',
        'BluePen': 'Pen',
        'RedPen': 'Pen',
        'WateredCan': 'Watering Can'
    }

    def __init__(self, node, is_procedural, procedural_distributions):
        self.node = node
        self.is_procedural = is_procedural
        self.procedural_distributions = procedural_distributions
        self.name = node[0]
        self.items = {}
        self.containers = set()

        if self.is_procedural:
            self.type = Distribution.TYPE_PROCEDURAL
        elif self.name == Distribution.NAME_ALL:
            self.type = Distribution.TYPE_META
        else:
            self.type = Distribution.TYPE_ROOM
            for node in node[1].items():
                container_id = node[0]
                if container_id == Distribution.KEY_ITEMS:
                    self.type = Distribution.TYPE_CONTAINER
                    break

        if self.type == Distribution.TYPE_ROOM:
            self.populate_room()
        elif self.type == Distribution.TYPE_CONTAINER or self.type == Distribution.TYPE_PROCEDURAL:
            self.populate_container()
        elif self.type == Distribution.TYPE_META:
            self.populate_meta()
        else:
            print('Unrecognized type: ' + self.type)

    def populate_room(self):
        for distribution_node in self.node[1].items():
            container_id = distribution_node[0]
            container_node = distribution_node[1]

            if str(lupa.lua_type(container_node)) != Distribution.LUA_TYPE_TABLE:
                continue

            items = None
            items_procedural = None
            items_junk = None

            for container_node_property_key, container_node_property_value in container_node.items():
                if container_node_property_key == Distribution.KEY_ITEMS:
                    items = container_node_property_value
                elif container_node_property_key == Distribution.KEY_PROCEDURAL:
                    items_procedural = container_node_property_value
                elif container_node_property_key == Distribution.KEY_JUNK:
                    items_junk = container_node_property_value

            if items:
                is_value = True
                for item_id in items.values():
                    if is_value:
                        self.add_item(item_id, container_id)
                    is_value = not is_value
            elif items_procedural:
                for item_procedural in items_procedural.values():
                    for distribution_procedural in self.procedural_distributions:
                        if item_procedural.name == distribution_procedural.name:
                            for item in distribution_procedural.items:
                                self.add_item(item, container_id, False)

    def populate_container(self):
        for distribution_node in self.node[1].items():
            container_id = distribution_node[0]
            container_node = distribution_node[1]

            if container_id != Distribution.KEY_ITEMS or str(lupa.lua_type(container_node)) != Distribution.LUA_TYPE_TABLE:
                continue

            is_value = True
            for item_id in container_node.values():
                if is_value:
                    self.add_item(item_id, container_id)

                is_value = not is_value

    def populate_meta(self):
        return

    def add_item(self, item_id, container_id, cleanup=True):
        if cleanup:
            item_id = self.cleanup_id(item_id)

        container_id = self.cleanup_id(container_id)

        item = self.items.get(item_id)

        if item is None:
            item = Item(item_id)
            self.items[item_id] = item

        item.containers.add(container_id)
        self.containers.add(container_id)

    def cleanup_id(self, id):
        id_pre_translation_entry = Distribution.ITEM_ID_PRE_TRANSLATION.get(id)

        if id_pre_translation_entry:
            return id_pre_translation_entry

        for blacklist_entry in Distribution.ITEM_ID_BLACKLIST:
            id = id.replace(blacklist_entry, '')

        trim_digits = True

        for blacklist_entry in Distribution.ITEM_ID_INTEGER_TRUNCATE_BLACKLIST_AGGRESSIVE:
            if blacklist_entry in id:
                trim_digits = False
                break

        if trim_digits:
            id = id.rstrip(string.digits)

        aggressive_translation_applied = False
        for key, value in Distribution.ITEM_ID_TRANSLATION_AGGRESSIVE.items():
            if key in id:
                id = value
                aggressive_translation_applied = True
                break

        if not aggressive_translation_applied:
            id_translation = Distribution.ITEM_ID_TRANSLATION.get(id)

            if id_translation:
                id = id_translation
            else:
                if ' ' not in id:
                    id = id.replace('_', '')
                    id = re.sub(r'(\w)([A-Z])', r'\1 \2', id)

        return id