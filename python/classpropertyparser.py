from cssutils import parseString
from string import ascii_lowercase, digits
# custom
from cssvalueparser import CSSPropertyValueParser
from datalibrary import ordered_property_dict, property_alias_dict
__author__ = 'chad nelson'
__project__ = 'blow dry css'


class ClassPropertyParser(object):
    # CSS Unit Reference: http://www.w3schools.com/cssref/css_units.asp
    # CSS Value Reference: http://www.w3.org/TR/CSS21/propidx.html
    def __init__(self, class_set=set()):
        css = u'''/* Generated with blowdrycss. */'''
        self.sheet = parseString(css)
        self.rules = []
        self.importance_designator = '-i'       # '-i' is used to designate that the priority level is '!important'
        self.removed_class_set = set()
        self.class_set = class_set
        self.clean_class_set()
        # print('clean ran')

    # Take list, tuple, or set of strings an convert to lowercase.
    def class_set_to_lowercase(self):
        self.class_set = {css_class.lower() for css_class in self.class_set}

    # Validate underscore usage in a single css_class.
    # Underscores are only allowed to designate a decimal point between numbers.
    #   Valid: '6_3'
    # Invalid: '_b', 'b_', 'padding-_2", '2_rem', 'm_px', and '__'
    @staticmethod
    def underscores_valid(css_class=''):
        # underscore is not allowed to be the first or last character of css_class
        if css_class[0] == '_' or css_class[-1] == '_':
            return False

        # Check character before and after underscore index.
        index = css_class.find('_')
        allowed_before = set(digits)
        allowed_after = set(digits)
        if index > 0:                                                   # Underscore is not the first character.
            valid = set(css_class[index-1]) <= allowed_before           # Check Character before
            valid = valid and set(css_class[index+1]) <= allowed_after  # Check Character after.
        else:
            valid = True

        return valid

    # Detect and Remove invalid css classes from class_set
    # Class names must abide by: http://www.w3.org/TR/CSS2/syndata.html#characters
    # For purposes of this project only a SUBSET of the standard is permissible as follows:
    # Encoded classes are only allowed to begin with [a-z]
    # Encoded classes are only allowed to end with [a-z0-9]
    # Encoded classes are allowed to contain [_a-z0-9-]
    # Underscores are only allowed between digits [0-9]
    # Reference: stackoverflow.com/questions/1323364/in-python-how-to-check-if-a-string-only-contains-certain-characters
    def clean_class_set(self):
        # Set all strings to lowercase first.
        self.class_set_to_lowercase()

        # Validate against character sets.
        allowed_first = set(ascii_lowercase)
        allowed_middle = set(ascii_lowercase + digits + '_-')
        allowed_last = set(ascii_lowercase + digits)

        # Gather invalid_css_classes
        invalid_css_classes = []
        reasons = []

        # 'continue' is used to prevent the same css_class from being added to the invalid_css_classes multiple times.
        for css_class in self.class_set:
            if not set(css_class[0]) <= allowed_first:              # First character
                invalid_css_classes.append(css_class)
                reasons.append(' (Only a-z allowed for first character of class.)')
                continue
            if not set(css_class) <= allowed_middle:                # All characters
                invalid_css_classes.append(css_class)
                reasons.append(' (Only a-z, 0-9, "_", and "-" are allowed in class name.)')
                continue
            if not set(css_class[-1]) <= allowed_last:              # Last character
                invalid_css_classes.append(css_class)
                reasons.append(' (Only a-z and 0-9 allowed for last character of class.)')
                continue
            if not self.underscores_valid(css_class=css_class):     # Underscore
                invalid_css_classes.append(css_class)
                reasons.append(' (Invalid underscore usage in class.)')
                continue

        # Remove invalid_css_classes from self.class_set
        for i, invalid_css_class in enumerate(invalid_css_classes):
            self.class_set.remove(invalid_css_class)
            self.removed_class_set.add(invalid_css_class + reasons[i])

    # Property Name
    #
    # Class returns the property_name or removes/cleans the unrecognized class and returns ''.
    # Classes that use identical property names must set a property value
    # i.e. 'font-weight' is invalid because no value is included AND 'font-weight-700' is valid because 700 is a value.
    @staticmethod
    def get_property_name(css_class=''):
        for property_name, aliases in ordered_property_dict.items():
            # Try identical key match first. An exact css_class match must also end with a '-' dash to be valid.
            if css_class.startswith(property_name + '-'):
                return property_name

            # Sort the aliases by descending string length
            # This is necessary when the css_class == 'bolder' since 'bold' appears before 'bolder'
            aliases = sorted(aliases, key=len, reverse=True)

            # Try matching with alias. An alias is not required to end with a dash, but could if it is an abbreviation.
            for alias in aliases:
                if css_class.startswith(alias):
                    return property_name

        # No match found.
        return ''

    # Strip property name from encoded_property_value if applicable and return encoded_property_value.
    @staticmethod
    def strip_property_name(property_name='', encoded_property_value=''):
        # Deny empty string. If it doesn't have a property name ignore it.
        if property_name == '':
            raise ValueError('CSS property_name cannot be empty.')
        # Append '-' to property to match the class format.
        else:
            property_name += '-'

        # Strip property name
        if encoded_property_value.startswith(property_name):
            return encoded_property_value[len(property_name):]
        else:
            return encoded_property_value

    # Some alias could be abbreviations e.g. 'fw-' stands for 'font-weight-'
    # In these cases a dash is added in the dictionary to indicate an abbreviation.
    @staticmethod
    def alias_is_abbreviation(alias=''):
        return alias.endswith('-')

    # Returns a list of all property abbreviations appearing in property_alias_dict
    def get_property_abbreviations(self, property_name=''):
        property_abbreviations = list()
        for alias in property_alias_dict[property_name]:
            if self.alias_is_abbreviation(alias=alias):
                property_abbreviations.append(alias)
        return property_abbreviations

    # Strip property abbreviation from encoded_property_value if applicable and return encoded_property_value.
    def strip_property_abbreviation(self, property_name='', encoded_property_value=''):
        property_abbreviations = self.get_property_abbreviations(property_name=property_name)

        for property_abbreviation in property_abbreviations:
            if encoded_property_value.startswith(property_abbreviation):
                return encoded_property_value[len(property_abbreviation):]
        return encoded_property_value

    # Property Value
    #
    # Strip property name or abbreviation prefix and property priority designator
    # Examples:
    # 'fw-bold-i' --> 'bold'                [abbreviated font-weight property_name]
    # 'padding-1-10-10-5-i' --> '1-10-10-5' [standard property_name]
    # 'height-7_25rem-i' --> '7_25rem'      [contains underscores]
    # The term encoded_property_value means a property value that may or may not contain dashes and underscores.
    def get_encoded_property_value(self, property_name='', css_class=''):
        encoded_property_value = css_class
        encoded_property_value = self.strip_property_name(property_name, encoded_property_value)
        encoded_property_value = self.strip_property_abbreviation(property_name, encoded_property_value)
        encoded_property_value = self.strip_priority_designator(encoded_property_value)
        return encoded_property_value

    # Accepts an encoded_property_value that's been stripped of it's property named and priority
    # Returns a valid css property value or ''.
    @staticmethod
    def get_property_value(property_name='', encoded_property_value=''):
        property_parser = CSSPropertyValueParser()
        value = property_parser.decode_property_value(property_name=property_name, value=encoded_property_value)
        return value

    # Property Priority
    #
    def is_important(self, css_class=''):
        return css_class.endswith(self.importance_designator)

    # Strip priority designator from the end of encoded_property_value.
    def strip_priority_designator(self, encoded_property_value=''):
        if self.is_important(css_class=encoded_property_value):
            return encoded_property_value[:-len(self.importance_designator)]
        else:
            return encoded_property_value

    def get_property_priority(self, css_class=''):
        return 'IMPORTANT' if self.is_important(css_class=css_class) else ''
