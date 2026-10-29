#!/usr/bin/env python3
"""
scripts/generate_all_data.py
Generates sql/002_data_en_US.sql and sql/003_data_de_DE.sql directly.
Guarantees 1-based contiguous indexing, large realistic pools, and exact pool_sizes.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"

def escape_sql(val: str) -> str:
    return str(val).replace("'", "''")

def write_inserts(f, table_name, cols, rows, batch_size=200):
    col_str = ", ".join(cols)
    for i in range(0, len(rows), batch_size):
        chunk = rows[i:i + batch_size]
        vals = []
        for r in chunk:
            items = []
            for item in r:
                if item is None:
                    items.append("NULL")
                elif isinstance(item, (int, float)):
                    items.append(str(item))
                else:
                    items.append(f"'{escape_sql(item)}'")
            vals.append(f"({', '.join(items)})")
        val_str = ",\n  ".join(vals)
        f.write(f"INSERT INTO {table_name} ({col_str}) VALUES\n  {val_str}\nON CONFLICT DO NOTHING;\n\n")

# --- US Data Pools ---
US_FIRST_MALE_SEEDS = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
    "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald", "Edward", "Jason", "Jeffrey", "Ryan",
    "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
    "Benjamin", "Samuel", "Gregory", "Alexander", "Frank", "Patrick", "Raymond", "Jack", "Dennis", "Jerry",
    "Tyler", "Aaron", "Jose", "Adam", "Nathan", "Henry", "Douglas", "Zachary", "Peter", "Kyle",
    "Walter", "Ethan", "Jeremy", "Harold", "Keith", "Christian", "Roger", "Noah", "Gerald", "Carl",
    "Terry", "Sean", "Austin", "Arthur", "Lawrence", "Jesse", "Dylan", "Bryan", "Joe", "Jordan",
    "Billy", "Bruce", "Albert", "Willie", "Gabriel", "Logan", "Alan", "Juan", "Wayne", "Roy",
    "Ralph", "Randy", "Eugene", "Vincent", "Russell", "Louis", "Philip", "Bobby", "Johnny", "Bradley",
    "Lucas", "Mason", "Oliver", "Elijah", "Aiden", "Liam", "Jackson", "Sebastian", "Caleb", "Owen",
    "Carter", "Jayden", "Johnathan", "Luke", "Isaac", "Levi", "Gavin", "Connor", "Wyatt", "Brayden",
    "Hunter", "Cameron", "Julian", "Jeremiah", "Max", "Eli", "Colton", "Dominic", "Cooper", "Cole",
    "Tristan", "Carson", "Ian", "Ashton", "Brody", "Blake", "Miles", "Leo", "Parker", "Chase",
    "Harrison", "Easton", "Bentley", "Gage", "Nolan", "Hudson", "Bryson", "Micah", "Sawyer", "Colin",
    "Adrian", "Derek", "Trevor", "Spencer", "Grant", "Dalton", "Garrett", "Preston", "Shawn", "Travis",
    "Shane", "Clifford", "Craig", "Glenn", "Curtis", "Corey", "Leonard", "Dustin", "Brett", "Mitchell",
    "Darrell", "Derrick", "Cody", "Wesley", "Dean", "Warren", "Troy", "Marcus", "Reginald", "Ruben",
    "Victor", "Martin", "Phillip", "Todd", "Jesse", "Lee", "Stanley", "Everett", "Lincoln", "Weston"
]

US_FIRST_FEMALE_SEEDS = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
    "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
    "Carol", "Amanda", "Dorothy", "Melissa", "Deborah", "Stephanie", "Rebecca", "Sharon", "Laura", "Cynthia",
    "Kathleen", "Amy", "Angela", "Shirley", "Anna", "Brenda", "Pamela", "Emma", "Nicole", "Helen",
    "Samantha", "Katherine", "Christine", "Debra", "Rachel", "Carolyn", "Janet", "Catherine", "Maria", "Heather",
    "Diane", "Ruth", "Julie", "Olivia", "Joyce", "Virginia", "Victoria", "Kelly", "Lauren", "Christina",
    "Joan", "Evelyn", "Judith", "Megan", "Andrea", "Cheryl", "Hannah", "Jacqueline", "Martha", "Gloria",
    "Teresa", "Ann", "Sara", "Madison", "Frances", "Kathryn", "Janice", "Jean", "Abigail", "Alice",
    "Julia", "Judy", "Sophia", "Grace", "Denise", "Amber", "Doris", "Marilyn", "Danielle", "Beverly",
    "Isabella", "Theresa", "Diana", "Natalie", "Brittany", "Charlotte", "Marie", "Kayla", "Alexis", "Lori",
    "Ava", "Mia", "Chloe", "Ella", "Harper", "Avery", "Addison", "Aubrey", "Stella", "Zoey",
    "Leah", "Audrey", "Savannah", "Claire", "Skylar", "Camila", "Penelope", "Paisley", "Nora", "Hazel",
    "Violet", "Aurora", "Ellie", "Scarlett", "Lillian", "Kinsley", "Lucy", "Elena", "Maya", "Naomi",
    "Riley", "Ariana", "Aaliyah", "Elliana", "Serenity", "Kennedy", "Madelyn", "Sadie", "Peyton", "Ruby",
    "Eva", "Piper", "Autumn", "Isla", "Quinn", "Delilah", "Cora", "Jade", "Clara", "Hadley",
    "Melanie", "Mackenzie", "Brooke", "Faith", "Brianna", "Valerie", "Paige", "Kylie", "Mariah", "Jenna",
    "Sienna", "Morgan", "Daisy", "Fiona", "Rose", "Genevieve", "Hope", "Esther", "Iris", "Joy",
    "Vivian", "Eloise", "Willow", "Ivy", "Lydia", "Amelia", "Harper", "Eleanor", "Phoebe", "Penelope"
]

US_LAST_SEEDS = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
    "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper",
    "Peterson", "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez",
    "Powell", "Jenkins", "Perry", "Russell", "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes",
    "Gonzales", "Fisher", "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham",
    "Reynolds", "Griffin", "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant", "Herrera", "Gibson",
    "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray", "Ford", "Castro", "Marshall", "Owens",
    "Harrison", "Fernandez", "McDonald", "Woods", "Washington", "Kennedy", "Wells", "Vargas", "Henry", "Chen",
    "Freeman", "Webb", "Tucker", "Guzman", "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter",
    "Gordon", "Mendez", "Silva", "Shaw", "Snyder", "Mason", "Dixon", "Muñoz", "Hunt", "Hicks",
    "Holmes", "Palmer", "Wagner", "Black", "Robertson", "Boyd", "Rose", "Stone", "Salazar", "Fox",
    "Warren", "Mills", "Meyer", "Rice", "Schmidt", "Garza", "Daniels", "Ferguson", "Nichols", "Stephens",
    "Soto", "Weaver", "Ryan", "Gardner", "Payne", "Grant", "Dunn", "Kelley", "Spencer", "Hawkins",
    "Arnold", "Pierce", "Vazquez", "Hansen", "Peters", "Santos", "Hart", "Bradley", "Knight", "Elliott",
    "Cunningham", "Duncan", "Armstrong", "Hudson", "Carroll", "Lane", "Riley", "Andrews", "Alvarado", "Ray",
    "Delgado", "Berry", "Perkins", "Hoffman", "Johnston", "Matthews", "Pena", "Richards", "Contreras", "Willis",
    "Carpenter", "Lawrence", "Sandoval", "Guerrero", "George", "Chapman", "Rios", "Estrada", "Ortega", "Watkins"
]

US_STREETS_SEEDS = [
    "Main", "Maple", "Oak", "Pine", "Cedar", "Elm", "Washington", "Lake", "Hill", "Park",
    "Walnut", "Spring", "North", "Ridge", "Lincoln", "Church", "Willow", "Mill", "Sunset", "Highland",
    "Chestnut", "Franklin", "Jefferson", "Jackson", "Adams", "Wilson", "Broadway", "Center", "River", "Meadow",
    "Valley", "Forest", "Green", "View", "Summit", "Hickory", "Cherry", "Cypress", "Poplar", "Beech",
    "Magnolia", "Spruce", "Sycamore", "Birch", "Ash", "Locust", "Linden", "Dogwood", "Laurel", "Orchard",
    "Vine", "Garden", "Woodland", "Fairview", "Pleasant", "Prospect", "Union", "Liberty", "Grand", "Central",
    "Market", "Pearl", "Water", "Bridge", "Front", "State", "Commercial", "Court", "College", "School",
    "Academy", "Cemetery", "Depot", "Station", "Railroad", "Factory", "Riverview", "Riverside", "Hillcrest", "Overlook",
    "Sunnyside", "Woodlawn", "Brookside", "Clearview", "Lakeview", "Mountain", "Canyon", "Prairie", "Stone", "Rock",
    "Pebble", "Creek", "Brook", "Run", "Crest", "Bluff", "Terrace", "Glen", "Hollow", "Ridgeview",
    "Fox", "Deer", "Eagle", "Falcon", "Hawk", "Quail", "Robin", "Sparrow", "Swallow", "Lark",
    "Briar", "Bramble", "Thorn", "Heather", "Fern", "Clover", "Moss", "Sage", "Ivy", "Holly"
]

def make_contiguous_pool(seeds, target_count, prefix_words=None, suffix_words=None):
    res = []
    seen = set()
    for s in seeds:
        if s not in seen:
            seen.add(s)
            res.append(s)
    
    if prefix_words:
        for p in prefix_words:
            for s in seeds:
                cand = f"{p} {s}"
                if cand not in seen:
                    seen.add(cand)
                    res.append(cand)
                if len(res) >= target_count:
                    return res[:target_count]
                    
    if suffix_words:
        for s in seeds:
            for suf in suffix_words:
                cand = f"{s} {suf}"
                if cand not in seen:
                    seen.add(cand)
                    res.append(cand)
                if len(res) >= target_count:
                    return res[:target_count]

    counter = 1
    while len(res) < target_count:
        cand = f"{seeds[counter % len(seeds)]} {counter}"
        if cand not in seen:
            seen.add(cand)
            res.append(cand)
        counter += 1
    return res[:target_count]

# Build US Pools
US_FIRST_MALE = make_contiguous_pool(US_FIRST_MALE_SEEDS, 1000, ["John", "Mark", "Paul", "Lee", "James", "Carl"])
US_FIRST_FEMALE = make_contiguous_pool(US_FIRST_FEMALE_SEEDS, 1000, ["Ann", "Marie", "Rose", "Grace", "Lynn", "Jane"])
US_LAST = make_contiguous_pool(US_LAST_SEEDS, 1200, None, ["Jr.", "II", "III", "IV", "V"])
US_STREETS = make_contiguous_pool(US_STREETS_SEEDS, 800, ["Old", "New", "North", "South", "East", "West", "Upper", "Lower"])

# 160 US Cities with realistic postal ranges and area codes
US_CITIES = [
    ("New York", "NY", 10001, 10282, "212"),
    ("Brooklyn", "NY", 11201, 11256, "718"),
    ("Queens", "NY", 11351, 11697, "718"),
    ("Buffalo", "NY", 14201, 14280, "716"),
    ("Rochester", "NY", 14602, 14692, "585"),
    ("Albany", "NY", 12201, 12288, "518"),
    ("Syracuse", "NY", 13201, 13290, "315"),
    ("Yonkers", "NY", 10701, 10710, "914"),
    ("White Plains", "NY", 10601, 10610, "914"),
    ("Los Angeles", "CA", 90001, 90089, "213"),
    ("San Francisco", "CA", 94101, 94188, "415"),
    ("San Diego", "CA", 92101, 92199, "619"),
    ("San Jose", "CA", 95101, 95196, "408"),
    ("Sacramento", "CA", 94203, 95899, "916"),
    ("Fresno", "CA", 93650, 93794, "559"),
    ("Long Beach", "CA", 90801, 90899, "562"),
    ("Oakland", "CA", 94601, 94666, "510"),
    ("Bakersfield", "CA", 93301, 93390, "661"),
    ("Anaheim", "CA", 92801, 92899, "714"),
    ("Santa Ana", "CA", 92701, 92799, "714"),
    ("Riverside", "CA", 92501, 92522, "951"),
    ("Irvine", "CA", 92602, 92623, "949"),
    ("Pasadena", "CA", 91101, 91110, "626"),
    ("Berkeley", "CA", 94701, 94720, "510"),
    ("Chicago", "IL", 60601, 60682, "312"),
    ("Aurora", "IL", 60502, 60598, "630"),
    ("Naperville", "IL", 60540, 60567, "630"),
    ("Rockford", "IL", 61101, 61126, "815"),
    ("Springfield", "IL", 62701, 62796, "217"),
    ("Peoria", "IL", 61601, 61656, "309"),
    ("Elgin", "IL", 60120, 60124, "847"),
    ("Waukegan", "IL", 60085, 60087, "847"),
    ("Champaign", "IL", 61820, 61826, "217"),
    ("Houston", "TX", 77001, 77099, "713"),
    ("San Antonio", "TX", 78201, 78299, "210"),
    ("Dallas", "TX", 75201, 75398, "214"),
    ("Austin", "TX", 78701, 78799, "512"),
    ("Fort Worth", "TX", 76101, 76199, "817"),
    ("El Paso", "TX", 79901, 79999, "915"),
    ("Arlington", "TX", 76001, 76096, "817"),
    ("Corpus Christi", "TX", 78401, 78480, "361"),
    ("Plano", "TX", 75023, 75094, "972"),
    ("Lubbock", "TX", 79401, 79499, "806"),
    ("Irving", "TX", 75014, 75064, "972"),
    ("Laredo", "TX", 78040, 78046, "956"),
    ("Amarillo", "TX", 79101, 79124, "806"),
    ("Waco", "TX", 76701, 76799, "254"),
    ("Phoenix", "AZ", 85001, 85099, "602"),
    ("Tucson", "AZ", 85701, 85775, "520"),
    ("Mesa", "AZ", 85201, 85277, "480"),
    ("Chandler", "AZ", 85224, 85286, "480"),
    ("Scottsdale", "AZ", 85250, 85271, "480"),
    ("Glendale", "AZ", 85301, 85318, "623"),
    ("Tempe", "AZ", 85280, 85287, "480"),
    ("Philadelphia", "PA", 19101, 19197, "215"),
    ("Pittsburgh", "PA", 15201, 15295, "412"),
    ("Allentown", "PA", 18101, 18195, "610"),
    ("Erie", "PA", 16501, 16554, "814"),
    ("Reading", "PA", 19601, 19612, "610"),
    ("Scranton", "PA", 18501, 18512, "570"),
    ("Miami", "FL", 33101, 33299, "305"),
    ("Orlando", "FL", 32801, 32899, "407"),
    ("Tampa", "FL", 33601, 33694, "813"),
    ("Jacksonville", "FL", 32099, 32277, "904"),
    ("Tallahassee", "FL", 32301, 32399, "850"),
    ("Fort Lauderdale", "FL", 33301, 33355, "954"),
    ("St. Petersburg", "FL", 33701, 33747, "727"),
    ("Hialeah", "FL", 33002, 33018, "305"),
    ("Gainesville", "FL", 32601, 32653, "352"),
    ("Atlanta", "GA", 30301, 30381, "404"),
    ("Augusta", "GA", 30901, 30999, "706"),
    ("Columbus", "GA", 31901, 31999, "706"),
    ("Savannah", "GA", 31401, 31421, "912"),
    ("Athens", "GA", 30601, 30612, "706"),
    ("Macon", "GA", 31201, 31297, "478"),
    ("Seattle", "WA", 98101, 98199, "206"),
    ("Spokane", "WA", 99201, 99299, "509"),
    ("Tacoma", "WA", 98401, 98499, "253"),
    ("Vancouver", "WA", 98660, 98687, "360"),
    ("Bellevue", "WA", 98004, 98009, "425"),
    ("Everett", "WA", 98201, 98213, "425"),
    ("Denver", "CO", 80201, 80299, "303"),
    ("Colorado Springs", "CO", 80901, 80997, "719"),
    ("Aurora", "CO", 80010, 80047, "303"),
    ("Fort Collins", "CO", 80521, 80553, "970"),
    ("Boulder", "CO", 80301, 80314, "303"),
    ("Lakewood", "CO", 80215, 80236, "303"),
    ("Boston", "MA", 2108, 2298, "617"),
    ("Worcester", "MA", 1601, 1655, "508"),
    ("Springfield", "MA", 1101, 1199, "413"),
    ("Cambridge", "MA", 2138, 2142, "617"),
    ("Lowell", "MA", 1850, 1854, "978"),
    ("Detroit", "MI", 48201, 48288, "313"),
    ("Grand Rapids", "MI", 49501, 49599, "616"),
    ("Warren", "MI", 48088, 48093, "586"),
    ("Ann Arbor", "MI", 48103, 48113, "734"),
    ("Lansing", "MI", 48901, 48980, "517"),
    ("Flint", "MI", 48501, 48557, "810"),
    ("Minneapolis", "MN", 55401, 55488, "612"),
    ("Saint Paul", "MN", 55101, 55188, "651"),
    ("Rochester", "MN", 55901, 55906, "507"),
    ("Duluth", "MN", 55801, 55816, "218"),
    ("Bloomington", "MN", 55420, 55439, "952"),
    ("Charlotte", "NC", 28201, 28299, "704"),
    ("Raleigh", "NC", 27601, 27699, "919"),
    ("Greensboro", "NC", 27401, 27499, "336"),
    ("Durham", "NC", 27701, 27722, "919"),
    ("Winston-Salem", "NC", 27101, 27199, "336"),
    ("Fayetteville", "NC", 28301, 28314, "910"),
    ("Cary", "NC", 27511, 27519, "919"),
    ("Columbus", "OH", 43085, 43291, "614"),
    ("Cleveland", "OH", 44101, 44199, "216"),
    ("Cincinnati", "OH", 45201, 45299, "513"),
    ("Toledo", "OH", 43601, 43699, "419"),
    ("Akron", "OH", 44301, 44398, "330"),
    ("Dayton", "OH", 45401, 45490, "937"),
    ("Canton", "OH", 44701, 44735, "330"),
    ("Youngstown", "OH", 44501, 44515, "330"),
    ("Indianapolis", "IN", 46201, 46298, "317"),
    ("Fort Wayne", "IN", 46801, 46899, "260"),
    ("Evansville", "IN", 47701, 47750, "812"),
    ("South Bend", "IN", 46601, 46699, "574"),
    ("Carmel", "IN", 46032, 46082, "317"),
    ("Bloomington", "IN", 47401, 47408, "812"),
    ("Nashville", "TN", 37201, 37250, "615"),
    ("Memphis", "TN", 38101, 38197, "901"),
    ("Knoxville", "TN", 37901, 37998, "865"),
    ("Chattanooga", "TN", 37401, 37450, "423"),
    ("Clarksville", "TN", 37040, 37044, "931"),
    ("Murfreesboro", "TN", 37127, 37133, "615"),
    ("Kansas City", "MO", 64101, 64199, "816"),
    ("Saint Louis", "MO", 63101, 63199, "314"),
    ("Springfield", "MO", 65801, 65899, "417"),
    ("Columbia", "MO", 65201, 65218, "573"),
    ("Independence", "MO", 64050, 64058, "816"),
    ("Baltimore", "MD", 21201, 21298, "410"),
    ("Frederick", "MD", 21701, 21705, "301"),
    ("Rockville", "MD", 20847, 20857, "301"),
    ("Gaithersburg", "MD", 20877, 20885, "301"),
    ("Milwaukee", "WI", 53201, 53295, "414"),
    ("Madison", "WI", 53701, 53794, "608"),
    ("Green Bay", "WI", 54301, 54344, "920"),
    ("Kenosha", "WI", 53140, 53144, "262"),
    ("Albuquerque", "NM", 87101, 87199, "505"),
    ("Las Cruces", "NM", 88001, 88013, "575"),
    ("Santa Fe", "NM", 87501, 87594, "505"),
    ("Las Vegas", "NV", 89101, 89199, "702"),
    ("Henderson", "NV", 89002, 89077, "702"),
    ("Reno", "NV", 89501, 89599, "775"),
    ("Portland", "OR", 97201, 97299, "503"),
    ("Salem", "OR", 97301, 97314, "503"),
    ("Eugene", "OR", 97401, 97440, "541"),
    ("Oklahoma City", "OK", 73101, 73199, "405"),
    ("Tulsa", "OK", 74101, 74194, "918"),
    ("Norman", "OK", 73019, 73072, "405"),
    ("Louisville", "KY", 40201, 40299, "502"),
    ("Lexington", "KY", 40502, 40598, "859"),
    ("Richmond", "VA", 23218, 23298, "804"),
    ("Virginia Beach", "VA", 23450, 23467, "757"),
    ("Norfolk", "VA", 23501, 23551, "757"),
    ("New Orleans", "LA", 70112, 70195, "504"),
    ("Baton Rouge", "LA", 70801, 70898, "225"),
    ("Hartford", "CT", 6101, 6199, "860"),
    ("Bridgeport", "CT", 6601, 6673, "203"),
    ("Salt Lake City", "UT", 84101, 84199, "801"),
    ("Birmingham", "AL", 35201, 35298, "205"),
    ("Honolulu", "HI", 96801, 96850, "808"),
    ("Anchorage", "AK", 99501, 99524, "907"),
    ("Boise", "ID", 83701, 83799, "208"),
    ("Omaha", "NE", 68101, 68198, "402"),
    ("Wichita", "KS", 67201, 67278, "316"),
    ("Des Moines", "IA", 50301, 50398, "515"),
    ("Little Rock", "AR", 72201, 72295, "501"),
    ("Jackson", "MS", 39201, 39298, "601"),
    ("Providence", "RI", 2901, 2940, "401"),
    ("Sioux Falls", "SD", 57101, 57198, "605"),
    ("Fargo", "ND", 58102, 58126, "701"),
    ("Charleston", "SC", 29401, 29492, "843"),
    ("Burlington", "VT", 5401, 5408, "802"),
    ("Manchester", "NH", 3101, 3111, "603"),
    ("Portland", "ME", 4101, 4124, "207"),
    ("Billings", "MT", 59101, 59117, "406"),
    ("Cheyenne", "WY", 82001, 82010, "307"),
    ("Wilmington", "DE", 19801, 19899, "302"),
    ("Charleston", "WV", 25301, 25396, "304")
]

print("Building en_US SQL file...")
with open(SQL_DIR / "002_data_en_US.sql", "w", encoding="utf-8") as f:
    f.write("-- =============================================================================\n")
    f.write("-- 002_data_en_US.sql  — Lookup data for en_US (English / United States)\n")
    f.write("-- Generated with contiguous 1-based indexing for 100k-1M fake user generation\n")
    f.write("-- =============================================================================\n\n")
    f.write("BEGIN;\n\n")
    
    # Locales
    f.write("INSERT INTO locales (code, display_name, country_name) VALUES\n")
    f.write("  ('en_US', 'English (United States)', 'United States')\n")
    f.write("ON CONFLICT DO NOTHING;\n\n")
    
    # Names
    name_rows = []
    for idx, name in enumerate(US_FIRST_MALE, start=1):
        name_rows.append(('en_US', 'first_male', idx, name))
    for idx, name in enumerate(US_FIRST_FEMALE, start=1):
        name_rows.append(('en_US', 'first_female', idx, name))
    for idx, name in enumerate(US_LAST, start=1):
        name_rows.append(('en_US', 'last', idx, name))
    write_inserts(f, "names", ["locale", "kind", "idx", "value"], name_rows)
    
    # Streets
    street_rows = [('en_US', idx, s) for idx, s in enumerate(US_STREETS, start=1)]
    write_inserts(f, "streets", ["locale", "idx", "name"], street_rows)
    
    # Cities
    city_rows = [('en_US', idx, c[0], c[1], c[2], c[3], c[4]) for idx, c in enumerate(US_CITIES, start=1)]
    write_inserts(f, "cities", ["locale", "idx", "city", "region", "postal_min", "postal_max", "area_code"], city_rows)
    
    # Choices
    choices_data = [
        ('en_US', 'title_male', 1, 'Mr.', 60),
        ('en_US', 'title_male', 2, 'Dr.', 10),
        ('en_US', 'title_male', 3, 'Prof.', 5),
        ('en_US', 'title_male', 4, '', 25),
        ('en_US', 'title_female', 1, 'Ms.', 30),
        ('en_US', 'title_female', 2, 'Mrs.', 25),
        ('en_US', 'title_female', 3, 'Dr.', 10),
        ('en_US', 'title_female', 4, 'Prof.', 5),
        ('en_US', 'title_female', 5, '', 30),
        ('en_US', 'name_template', 1, '{first} {last}', 40),
        ('en_US', 'name_template', 2, '{title} {first} {last}', 20),
        ('en_US', 'name_template', 3, '{first} {mi}. {last}', 20),
        ('en_US', 'name_template', 4, '{title} {first} {middle} {last}', 10),
        ('en_US', 'name_template', 5, '{first} {middle} {last}', 10),
        ('en_US', 'addr_template', 1, '{num} {street}, {city}, {region} {postal}', 60),
        ('en_US', 'addr_template', 2, '{num} {street}, Apt {unit}, {city}, {region} {postal}', 20),
        ('en_US', 'addr_template', 3, '{num} {street}, Suite {unit}, {city}, {region} {postal}', 10),
        ('en_US', 'addr_template', 4, '{num} {street}, Unit {unit}, {city}, {region} {postal}', 10),
        ('en_US', 'street_type', 1, 'Ave', 30),
        ('en_US', 'street_type', 2, 'St', 30),
        ('en_US', 'street_type', 3, 'Blvd', 15),
        ('en_US', 'street_type', 4, 'Dr', 15),
        ('en_US', 'street_type', 5, 'Ln', 10),
        ('en_US', 'street_type', 6, 'Ct', 8),
        ('en_US', 'street_type', 7, 'Pl', 8),
        ('en_US', 'street_type', 8, 'Rd', 10),
        ('en_US', 'street_type', 9, 'Way', 5),
        ('en_US', 'street_type', 10, 'Circle', 4),
        ('en_US', 'phone_template', 1, '({area}) 555-01##', 50),
        ('en_US', 'phone_template', 2, '({area}) 555-02##', 30),
        ('en_US', 'phone_template', 3, '+1 ({area}) 555-01##', 20),
        ('en_US', 'email_sep', 1, '.', 40),
        ('en_US', 'email_sep', 2, '_', 30),
        ('en_US', 'email_sep', 3, '', 30),
        ('en_US', 'email_num', 1, '', 50),
        ('en_US', 'email_num', 2, '##', 25),
        ('en_US', 'email_num', 3, '###', 15),
        ('en_US', 'email_num', 4, '####', 10),
        ('en_US', 'email_domain', 1, 'gmail.com', 35),
        ('en_US', 'email_domain', 2, 'yahoo.com', 20),
        ('en_US', 'email_domain', 3, 'hotmail.com', 15),
        ('en_US', 'email_domain', 4, 'outlook.com', 10),
        ('en_US', 'email_domain', 5, 'icloud.com', 8),
        ('en_US', 'email_domain', 6, 'protonmail.com', 7),
        ('en_US', 'email_domain', 7, 'aol.com', 5),
        ('en_US', 'eye_color', 1, 'Brown', 45),
        ('en_US', 'eye_color', 2, 'Blue', 27),
        ('en_US', 'eye_color', 3, 'Green', 18),
        ('en_US', 'eye_color', 4, 'Hazel', 6),
        ('en_US', 'eye_color', 5, 'Gray', 4)
    ]
    write_inserts(f, "choices", ["locale", "category", "ord", "value", "weight"], choices_data)
    
    # Body params
    body_data = [
        ('en_US', 'male', 'height_cm', 176.0, 7.0, 140.0, 220.0),
        ('en_US', 'male', 'weight_kg', 88.0, 15.0, 40.0, 200.0),
        ('en_US', 'female', 'height_cm', 162.0, 6.5, 130.0, 210.0),
        ('en_US', 'female', 'weight_kg', 75.0, 14.0, 35.0, 180.0)
    ]
    write_inserts(f, "body_params", ["locale", "gender", "attribute", "mean", "sd", "min_val", "max_val"], body_data)
    
    # Translit
    translit_data = [
        ('en_US', 'é', 'e'), ('en_US', 'è', 'e'), ('en_US', 'ê', 'e'), ('en_US', 'ë', 'e'),
        ('en_US', 'à', 'a'), ('en_US', 'â', 'a'), ('en_US', 'ä', 'a'), ('en_US', 'ô', 'o'),
        ('en_US', 'ö', 'o'), ('en_US', 'ü', 'u'), ('en_US', 'ú', 'u'), ('en_US', 'ù', 'u'),
        ('en_US', 'ñ', 'n'), ('en_US', 'ç', 'c')
    ]
    write_inserts(f, "translit", ["locale", "from_str", "to_str"], translit_data)
    
    # Pool sizes
    f.write("INSERT INTO pool_sizes (locale, pool, size) VALUES\n")
    f.write(f"  ('en_US', 'first_male', {len(US_FIRST_MALE)}),\n")
    f.write(f"  ('en_US', 'first_female', {len(US_FIRST_FEMALE)}),\n")
    f.write(f"  ('en_US', 'last', {len(US_LAST)}),\n")
    f.write(f"  ('en_US', 'streets', {len(US_STREETS)}),\n")
    f.write(f"  ('en_US', 'cities', {len(US_CITIES)})\n")
    f.write("ON CONFLICT (locale, pool) DO UPDATE SET size = EXCLUDED.size;\n\n")
    
    f.write("COMMIT;\n")

print("en_US data generated successfully.")


# --- de_DE Data Pools ---
DE_FIRST_MALE_SEEDS = [
    "Hans", "Klaus", "Peter", "Michael", "Thomas", "Andreas", "Stefan", "Wolfgang", "Jürgen", "Uwe",
    "Dieter", "Frank", "Bernd", "Werner", "Helmut", "Manfred", "Gerhard", "Heinz", "Walter", "Horst",
    "Martin", "Christian", "Dirk", "Jörg", "Markus", "Alexander", "Sven", "Jens", "Holger", "Torsten",
    "Jan", "Oliver", "Daniel", "Florian", "Sebastian", "Tobias", "Philipp", "Patrick", "Lukas", "Leon",
    "Felix", "Maximilian", "Jonas", "Paul", "Tim", "David", "Niklas", "Finn", "Elias", "Julian",
    "Moritz", "Simon", "Ben", "Noah", "Luca", "Fabian", "Moritz", "Matthias", "Carsten", "Rainer",
    "Ralf", "Roland", "Norbert", "Reinhard", "Joachim", "Volker", "Hartmut", "Achim", "Alfred", "Bernhard",
    "Christoph", "Clemens", "Dominik", "Eberhard", "Eckhard", "Ernst", "Friedrich", "Georg", "Gerd", "Gottfried",
    "Gregor", "Guido", "Gunther", "Hannes", "Harald", "Heiko", "Hendrik", "Henning", "Herbert", "Hermann",
    "Ingo", "Jakob", "Jochen", "Johannes", "Josef", "Kai", "Karl", "Karsten", "Knut", "Konrad",
    "Kurt", "Lars", "Lennart", "Ludwig", "Lutz", "Manuel", "Marc", "Marcel", "Marco", "Mario",
    "Marius", "Max", "Nico", "Nils", "Olaf", "Pascal", "Rene", "Richard", "Robert", "Robin",
    "Roman", "Sascha", "Steffen", "Stephan", "Sönke", "Thilo", "Thorsten", "Till", "Timo", "Tom",
    "Ulrich", "Valentin", "Viktor", "Vincent", "Waldemar", "Wilhelm", "Willi", "Wilfried", "Yannick", "Anton"
]

DE_FIRST_FEMALE_SEEDS = [
    "Ursula", "Helga", "Karin", "Ingrid", "Renate", "Brigitte", "Erika", "Gisela", "Monika", "Christa",
    "Elke", "Hannelore", "Barbara", "Gertrud", "Elisabeth", "Maria", "Angelika", "Gabriele", "Marion", "Birgit",
    "Petra", "Andrea", "Sabine", "Claudia", "Susanne", "Heike", "Martina", "Anke", "Bettina", "Nicole",
    "Stefanie", "Tanja", "Melanie", "Sandra", "Katja", "Julia", "Nadine", "Sarah", "Jessica", "Christina",
    "Jennifer", "Laura", "Anna", "Lisa", "Katharina", "Vanessa", "Lena", "Lea", "Marie", "Hannah",
    "Sophie", "Emily", "Mia", "Emma", "Lina", "Mila", "Ella", "Clara", "Luisa", "Johanna",
    "Amelie", "Nele", "Charlotte", "Frieda", "Ida", "Mathilda", "Lilly", "Paula", "Maja", "Pia",
    "Greta", "Theresa", "Victoria", "Antonia", "Carla", "Elena", "Franziska", "Helena", "Isabel", "Jana",
    "Jasmin", "Klara", "Larissa", "Livia", "Magdalena", "Mara", "Miriam", "Pauline", "Romy", "Selina",
    "Sina", "Stella", "Valerie", "Astrid", "Beate", "Carolin", "Dagmar", "Daniela", "Doris", "Dorothea",
    "Edith", "Eva", "Frauke", "Gudrun", "Hanna", "Ines", "Irene", "Iris", "Isabell", "Judith",
    "Jutta", "Kerstin", "Kornelia", "Kristin", "Manuela", "Margret", "Meike", "Michaela", "Rita", "Silke"
]

DE_LAST_SEEDS = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
    "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf", "Schröder", "Neumann", "Schwarz", "Zimmermann",
    "Braun", "Krüger", "Hofmann", "Hartmann", "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier",
    "Lehmann", "Schmid", "Schulze", "Maier", "Köhler", "Herrmann", "König", "Walter", "Mayer", "Huber",
    "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung", "Hahn", "Schubert",
    "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger", "Winkler", "Roth", "Beck", "Lorenz",
    "Baumann", "Franke", "Albrecht", "Schuster", "Simon", "Ludwig", "Böhm", "Winter", "Kraus", "Martin",
    "Krämer", "Vogt", "Stein", "Jäger", "Otto", "Sommer", "Groß", "Seidel", "Heinrich", "Brandt",
    "Haas", "Schreiber", "Graf", "Schulte", "Dietrich", "Ziegler", "Kuhn", "Pohl", "Engel", "Horn",
    "Busch", "Bergmann", "Thomas", "Voigt", "Sauer", "Arnold", "Wolff", "Pfeifer", "Frey", "Beyer",
    "Vollmer", "Dittmann", "Kroll", "Stoll", "Barth", "Hein", "Ebert", "Fröhlich", "Kaufmann", "Reuter",
    "Ullrich", "Fiedler", "Götz", "Hesse", "Kunz", "Reichert", "Schilling", "Witt", "Bachmann", "Bode"
]

DE_STREETS_SEEDS = [
    "Haupt", "Garten", "Schul", "Bahnhof", "Dorf", "Berg", "Wald", "Kirch", "Linden", "Birken",
    "Wiesen", "Sonnen", "Goethe", "Schiller", "Mozart", "Beethoven", "Bach", "Rosen", "Blumen", "Eichen",
    "Buchen", "Tannen", "Ahorn", "Kastanien", "Flur", "Feld", "Brunnen", "Mühl", "Markt", "Post",
    "Ring", "Park", "Süd", "Nord", "West", "Ost", "Hoch", "Tal", "Anger", "Friedhof",
    "Hafen", "Industrie", "Mühlen", "Schloss", "Burg", "Turm", "Brücken", "Kanal", "Ufer", "See",
    "Teich", "Bach", "Quelle", "Felsen", "Stein", "Kies", "Sand", "Lehm", "Moor", "Heide",
    "Kiefern", "Ulmen", "Erlen", "Eschen", "Weiden", "Pappeln", "Hasel", "Holunder", "Flieder", "Nelken",
    "Tulpen", "Veilchen", "Lilien", "Dahlien", "Astern", "Jasmin", "Korn", "Gersten", "Weizen", "Roggen",
    "Hafer", "Hopfen", "Reben", "Weinberg", "Kloster", "Dom", "Kapellen", "Kreuz", "Pfarr", "Kant"
]

DE_FIRST_MALE = make_contiguous_pool(DE_FIRST_MALE_SEEDS, 1000, ["Hans", "Karl", "Peter", "Jan", "Lukas", "Paul"])
DE_FIRST_FEMALE = make_contiguous_pool(DE_FIRST_FEMALE_SEEDS, 1000, ["Anna", "Maria", "Sophie", "Marie", "Lisa", "Laura"])
DE_LAST = make_contiguous_pool(DE_LAST_SEEDS, 1200, None, ["sen.", "jun.", "von", "zu", "der"])
DE_STREETS = make_contiguous_pool(DE_STREETS_SEEDS, 800, ["Alte", "Neue", "Obere", "Untere", "Große", "Kleine", "Hintere", "Vordere"])

DE_CITIES = [
    ("Berlin", "Berlin", 10115, 14199, "30"),
    ("Hamburg", "Hamburg", 20095, 22769, "40"),
    ("München", "Bayern", 80331, 81929, "89"),
    ("Köln", "Nordrhein-Westfalen", 50667, 51149, "221"),
    ("Frankfurt am Main", "Hessen", 60306, 60599, "69"),
    ("Stuttgart", "Baden-Württemberg", 70173, 70629, "711"),
    ("Düsseldorf", "Nordrhein-Westfalen", 40210, 40629, "211"),
    ("Leipzig", "Sachsen", 4103, 4357, "341"),
    ("Dortmund", "Nordrhein-Westfalen", 44135, 44388, "231"),
    ("Essen", "Nordrhein-Westfalen", 45127, 45359, "201"),
    ("Bremen", "Bremen", 28195, 28779, "421"),
    ("Dresden", "Sachsen", 1067, 1328, "351"),
    ("Hannover", "Niedersachsen", 30159, 30669, "511"),
    ("Nürnberg", "Bayern", 90402, 90491, "911"),
    ("Duisburg", "Nordrhein-Westfalen", 47051, 47279, "203"),
    ("Bochum", "Nordrhein-Westfalen", 44787, 44894, "234"),
    ("Wuppertal", "Nordrhein-Westfalen", 42103, 42399, "202"),
    ("Bielefeld", "Nordrhein-Westfalen", 33602, 33739, "521"),
    ("Bonn", "Nordrhein-Westfalen", 53111, 53229, "228"),
    ("Münster", "Nordrhein-Westfalen", 48143, 48167, "251"),
    ("Karlsruhe", "Baden-Württemberg", 76131, 76229, "721"),
    ("Mannheim", "Baden-Württemberg", 68159, 68309, "621"),
    ("Augsburg", "Bayern", 86150, 86199, "821"),
    ("Wiesbaden", "Hessen", 65183, 65207, "611"),
    ("Gelsenkirchen", "Nordrhein-Westfalen", 45879, 45899, "209"),
    ("Mönchengladbach", "Nordrhein-Westfalen", 41061, 41239, "2161"),
    ("Braunschweig", "Niedersachsen", 38100, 38126, "531"),
    ("Chemnitz", "Sachsen", 9111, 9131, "371"),
    ("Kiel", "Schleswig-Holstein", 24103, 24159, "431"),
    ("Aachen", "Nordrhein-Westfalen", 52062, 52080, "241"),
    ("Halle (Saale)", "Sachsen-Anhalt", 6108, 6132, "345"),
    ("Magdeburg", "Sachsen-Anhalt", 39104, 39130, "391"),
    ("Freiburg im Breisgau", "Baden-Württemberg", 79098, 79117, "761"),
    ("Krefeld", "Nordrhein-Westfalen", 47798, 47839, "2151"),
    ("Mainz", "Rheinland-Pfalz", 55116, 55131, "6131"),
    ("Lübeck", "Schleswig-Holstein", 23552, 23570, "451"),
    ("Erfurt", "Thüringen", 99084, 99198, "361"),
    ("Oberhausen", "Nordrhein-Westfalen", 46045, 46149, "208"),
    ("Rostock", "Mecklenburg-Vorpommern", 18055, 18147, "381"),
    ("Kassel", "Hessen", 34117, 34134, "561"),
    ("Hagen", "Nordrhein-Westfalen", 58089, 58135, "2331"),
    ("Potsdam", "Brandenburg", 14467, 14482, "331"),
    ("Saarbrücken", "Saarland", 66111, 66133, "681"),
    ("Hamm", "Nordrhein-Westfalen", 59063, 59077, "2381"),
    ("Ludwigshafen am Rhein", "Rheinland-Pfalz", 67059, 67071, "621"),
    ("Mülheim an der Ruhr", "Nordrhein-Westfalen", 45468, 45481, "208"),
    ("Oldenburg", "Niedersachsen", 26121, 26135, "441"),
    ("Osnabrück", "Niedersachsen", 49074, 49090, "541"),
    ("Leverkusen", "Nordrhein-Westfalen", 51371, 51381, "214"),
    ("Heidelberg", "Baden-Württemberg", 69115, 69126, "6221"),
    ("Darmstadt", "Hessen", 64283, 64297, "6151"),
    ("Solingen", "Nordrhein-Westfalen", 42651, 42719, "212"),
    ("Herne", "Nordrhein-Westfalen", 44623, 44653, "2323"),
    ("Regensburg", "Bayern", 93047, 93059, "941"),
    ("Neuss", "Nordrhein-Westfalen", 41460, 41472, "2131"),
    ("Paderborn", "Nordrhein-Westfalen", 33098, 33106, "5251"),
    ("Ingolstadt", "Bayern", 85049, 85057, "841"),
    ("Offenbach am Main", "Hessen", 63065, 63075, "69"),
    ("Fürth", "Bayern", 90762, 90768, "911"),
    ("Ulm", "Baden-Württemberg", 89073, 89081, "731"),
    ("Heilbronn", "Baden-Württemberg", 74072, 74081, "7131"),
    ("Pforzheim", "Baden-Württemberg", 75172, 75181, "7231"),
    ("Würzburg", "Bayern", 97070, 97084, "931"),
    ("Wolfsburg", "Niedersachsen", 38440, 38448, "5361"),
    ("Göttingen", "Niedersachsen", 37073, 37085, "551"),
    ("Bottrop", "Nordrhein-Westfalen", 46236, 46244, "2041"),
    ("Recklinghausen", "Nordrhein-Westfalen", 45657, 45665, "2361"),
    ("Reutlingen", "Baden-Württemberg", 72760, 72770, "7121"),
    ("Koblenz", "Rheinland-Pfalz", 56068, 56077, "261"),
    ("Bremerhaven", "Bremen", 27568, 27580, "471"),
    ("Bergisch Gladbach", "Nordrhein-Westfalen", 51427, 51469, "2202"),
    ("Jena", "Thüringen", 7743, 7751, "3641"),
    ("Remscheid", "Nordrhein-Westfalen", 42853, 42899, "2191"),
    ("Erlangen", "Bayern", 91052, 91058, "9131"),
    ("Moers", "Nordrhein-Westfalen", 47441, 47447, "2841"),
    ("Siegen", "Nordrhein-Westfalen", 57072, 57080, "271"),
    ("Hildesheim", "Niedersachsen", 31134, 31141, "5121"),
    ("Salzgitter", "Niedersachsen", 38226, 38259, "5341"),
    ("Cottbus", "Brandenburg", 3042, 3055, "355"),
    ("Kaiserslautern", "Rheinland-Pfalz", 67655, 67663, "631"),
    ("Gütersloh", "Nordrhein-Westfalen", 33330, 33335, "5241"),
    ("Schwerin", "Mecklenburg-Vorpommern", 19053, 19063, "385"),
    ("Witten", "Nordrhein-Westfalen", 58452, 58456, "2302"),
    ("Gera", "Thüringen", 7545, 7554, "365"),
    ("Iserlohn", "Nordrhein-Westfalen", 58636, 58644, "2371"),
    ("Ludwigsburg", "Baden-Württemberg", 71634, 71642, "7141"),
    ("Hanau", "Hessen", 63450, 63457, "6181"),
    ("Esslingen am Neckar", "Baden-Württemberg", 73728, 73734, "711"),
    ("Zwickau", "Sachsen", 8056, 8066, "375"),
    ("Düren", "Nordrhein-Westfalen", 52349, 52355, "2421"),
    ("Ratingen", "Nordrhein-Westfalen", 40878, 40885, "2102"),
    ("Tübingen", "Baden-Württemberg", 72070, 72076, "7071"),
    ("Flensburg", "Schleswig-Holstein", 24937, 24944, "461"),
    ("Lünen", "Nordrhein-Westfalen", 44532, 44536, "2306"),
    ("Villingen-Schwenningen", "Baden-Württemberg", 78048, 78056, "7721"),
    ("Gießen", "Hessen", 35390, 35398, "641"),
    ("Marl", "Nordrhein-Westfalen", 45768, 45772, "2365"),
    ("Dessau-Roßlau", "Sachsen-Anhalt", 6842, 6849, "340"),
    ("Konstanz", "Baden-Württemberg", 78462, 78467, "7531"),
    ("Worms", "Rheinland-Pfalz", 67547, 67551, "6241"),
    ("Minden", "Nordrhein-Westfalen", 32423, 32429, "571"),
    ("Velbert", "Nordrhein-Westfalen", 42549, 42555, "2051"),
    ("Norderstedt", "Schleswig-Holstein", 22844, 22851, "40"),
    ("Neumünster", "Schleswig-Holstein", 24534, 24539, "4321"),
    ("Delmenhorst", "Niedersachsen", 27749, 27755, "4221"),
    ("Wilhelmshaven", "Niedersachsen", 26382, 26389, "4421"),
    ("Viersen", "Nordrhein-Westfalen", 41747, 41751, "2162"),
    ("Gladbeck", "Nordrhein-Westfalen", 45964, 45968, "2043"),
    ("Dorsten", "Nordrhein-Westfalen", 46282, 46286, "2362"),
    ("Rheine", "Nordrhein-Westfalen", 48429, 48432, "5971"),
    ("Detmold", "Nordrhein-Westfalen", 32756, 32760, "5231"),
    ("Troisdorf", "Nordrhein-Westfalen", 53840, 53844, "2241"),
    ("Castrop-Rauxel", "Nordrhein-Westfalen", 44575, 44581, "2305"),
    ("Lüneburg", "Niedersachsen", 21335, 21339, "4131"),
    ("Bamberg", "Bayern", 96047, 96052, "951"),
    ("Arnsberg", "Nordrhein-Westfalen", 59755, 59823, "2931"),
    ("Bayreuth", "Bayern", 95444, 95448, "921"),
    ("Brandenburg an der Havel", "Brandenburg", 14770, 14776, "3381"),
    ("Bocholt", "Nordrhein-Westfalen", 46395, 46399, "2871"),
    ("Aschaffenburg", "Bayern", 63739, 63743, "6021"),
    ("Landshut", "Bayern", 84028, 84036, "871"),
    ("Kempten (Allgäu)", "Bayern", 87435, 87439, "831"),
    ("Fulda", "Hessen", 36037, 36043, "661"),
    ("Aalen", "Baden-Württemberg", 73430, 73434, "7361"),
    ("Lippstadt", "Nordrhein-Westfalen", 59555, 59558, "2941"),
    ("Dinslaken", "Nordrhein-Westfalen", 46535, 46539, "2064"),
    ("Herford", "Nordrhein-Westfalen", 32049, 32052, "5221"),
    ("Kerpen", "Nordrhein-Westfalen", 50169, 50171, "2237"),
    ("Rüsselsheim am Main", "Hessen", 65428, 65428, "6142"),
    ("Weimar", "Thüringen", 99423, 99428, "3643"),
    ("Plauen", "Sachsen", 8523, 8529, "3741"),
    ("Sindelfingen", "Baden-Württemberg", 71063, 71069, "7031"),
    ("Neubrandenburg", "Mecklenburg-Vorpommern", 17033, 17036, "395"),
    ("Dormagen", "Nordrhein-Westfalen", 41539, 41542, "2133"),
    ("Greifswald", "Mecklenburg-Vorpommern", 17489, 17493, "3834"),
    ("Rosenheim", "Bayern", 83022, 83028, "8031")
]

print("Building de_DE SQL file...")
with open(SQL_DIR / "003_data_de_DE.sql", "w", encoding="utf-8") as f:
    f.write("-- =============================================================================\n")
    f.write("-- 003_data_de_DE.sql  — Lookup data for de_DE (Deutsch / Deutschland)\n")
    f.write("-- Generated with contiguous 1-based indexing for 100k-1M fake user generation\n")
    f.write("-- =============================================================================\n\n")
    f.write("BEGIN;\n\n")
    
    # Locales
    f.write("INSERT INTO locales (code, display_name, country_name) VALUES\n")
    f.write("  ('de_DE', 'Deutsch (Deutschland)', 'Deutschland')\n")
    f.write("ON CONFLICT DO NOTHING;\n\n")
    
    # Names
    name_rows = []
    for idx, name in enumerate(DE_FIRST_MALE, start=1):
        name_rows.append(('de_DE', 'first_male', idx, name))
    for idx, name in enumerate(DE_FIRST_FEMALE, start=1):
        name_rows.append(('de_DE', 'first_female', idx, name))
    for idx, name in enumerate(DE_LAST, start=1):
        name_rows.append(('de_DE', 'last', idx, name))
    write_inserts(f, "names", ["locale", "kind", "idx", "value"], name_rows)
    
    # Streets
    street_rows = [('de_DE', idx, s) for idx, s in enumerate(DE_STREETS, start=1)]
    write_inserts(f, "streets", ["locale", "idx", "name"], street_rows)
    
    # Cities
    city_rows = [('de_DE', idx, c[0], c[1], c[2], c[3], c[4]) for idx, c in enumerate(DE_CITIES, start=1)]
    write_inserts(f, "cities", ["locale", "idx", "city", "region", "postal_min", "postal_max", "area_code"], city_rows)
    
    # Choices
    choices_data = [
        ('de_DE', 'title_male', 1, 'Herr', 60),
        ('de_DE', 'title_male', 2, 'Dr.', 15),
        ('de_DE', 'title_male', 3, 'Prof. Dr.', 5),
        ('de_DE', 'title_male', 4, '', 20),
        ('de_DE', 'title_female', 1, 'Frau', 60),
        ('de_DE', 'title_female', 2, 'Dr.', 15),
        ('de_DE', 'title_female', 3, 'Prof. Dr.', 5),
        ('de_DE', 'title_female', 4, '', 20),
        ('de_DE', 'name_template', 1, '{first} {last}', 40),
        ('de_DE', 'name_template', 2, '{title} {first} {last}', 30),
        ('de_DE', 'name_template', 3, '{first} {mi}. {last}', 15),
        ('de_DE', 'name_template', 4, '{title} {first} {middle} {last}', 8),
        ('de_DE', 'name_template', 5, '{first} {middle} {last}', 7),
        ('de_DE', 'addr_template', 1, '{street} {num}, {postal} {city}', 60),
        ('de_DE', 'addr_template', 2, '{street} {num}, OG {unit}, {postal} {city}', 15),
        ('de_DE', 'addr_template', 3, '{street} {num}, Wohnung {unit}, {postal} {city}', 15),
        ('de_DE', 'addr_template', 4, '{street} {num}, App. {unit}, {postal} {city}', 10),
        ('de_DE', 'street_type', 1, 'straße', 40),
        ('de_DE', 'street_type', 2, 'weg', 20),
        ('de_DE', 'street_type', 3, 'gasse', 10),
        ('de_DE', 'street_type', 4, 'allee', 10),
        ('de_DE', 'street_type', 5, 'platz', 8),
        ('de_DE', 'street_type', 6, 'ring', 7),
        ('de_DE', 'street_type', 7, 'damm', 5),
        ('de_DE', 'phone_template', 1, '+49 {area} ###-####', 40),
        ('de_DE', 'phone_template', 2, '+49 ({area}) ###-####', 30),
        ('de_DE', 'phone_template', 3, '0{area} ###-####', 20),
        ('de_DE', 'phone_template', 4, '({area}) ###-####', 10),
        ('de_DE', 'email_sep', 1, '.', 45),
        ('de_DE', 'email_sep', 2, '_', 30),
        ('de_DE', 'email_sep', 3, '', 25),
        ('de_DE', 'email_num', 1, '', 50),
        ('de_DE', 'email_num', 2, '##', 25),
        ('de_DE', 'email_num', 3, '###', 15),
        ('de_DE', 'email_num', 4, '####', 10),
        ('de_DE', 'email_domain', 1, 'gmail.com', 25),
        ('de_DE', 'email_domain', 2, 'web.de', 20),
        ('de_DE', 'email_domain', 3, 'gmx.de', 20),
        ('de_DE', 'email_domain', 4, 't-online.de', 10),
        ('de_DE', 'email_domain', 5, 'yahoo.de', 8),
        ('de_DE', 'email_domain', 6, 'hotmail.de', 7),
        ('de_DE', 'email_domain', 7, 'outlook.de', 10),
        ('de_DE', 'eye_color', 1, 'Braun', 45),
        ('de_DE', 'eye_color', 2, 'Blau', 30),
        ('de_DE', 'eye_color', 3, 'Grün', 15),
        ('de_DE', 'eye_color', 4, 'Grau', 7),
        ('de_DE', 'eye_color', 5, 'Haselnuss', 3)
    ]
    write_inserts(f, "choices", ["locale", "category", "ord", "value", "weight"], choices_data)
    
    # Body params
    body_data = [
        ('de_DE', 'male', 'height_cm', 177.0, 7.0, 140.0, 220.0),
        ('de_DE', 'male', 'weight_kg', 85.0, 14.0, 40.0, 200.0),
        ('de_DE', 'female', 'height_cm', 163.0, 6.5, 130.0, 210.0),
        ('de_DE', 'female', 'weight_kg', 72.0, 13.0, 35.0, 180.0)
    ]
    write_inserts(f, "body_params", ["locale", "gender", "attribute", "mean", "sd", "min_val", "max_val"], body_data)
    
    # Translit
    translit_data = [
        ('de_DE', 'ä', 'ae'), ('de_DE', 'ö', 'oe'), ('de_DE', 'ü', 'ue'),
        ('de_DE', 'Ä', 'Ae'), ('de_DE', 'Ö', 'Oe'), ('de_DE', 'Ü', 'Ue'),
        ('de_DE', 'ß', 'ss'), ('de_DE', 'é', 'e'),  ('de_DE', 'è', 'e'),
        ('de_DE', 'á', 'a'),  ('de_DE', 'à', 'a')
    ]
    write_inserts(f, "translit", ["locale", "from_str", "to_str"], translit_data)
    
    # Pool sizes
    f.write("INSERT INTO pool_sizes (locale, pool, size) VALUES\n")
    f.write(f"  ('de_DE', 'first_male', {len(DE_FIRST_MALE)}),\n")
    f.write(f"  ('de_DE', 'first_female', {len(DE_FIRST_FEMALE)}),\n")
    f.write(f"  ('de_DE', 'last', {len(DE_LAST)}),\n")
    f.write(f"  ('de_DE', 'streets', {len(DE_STREETS)}),\n")
    f.write(f"  ('de_DE', 'cities', {len(DE_CITIES)})\n")
    f.write("ON CONFLICT (locale, pool) DO UPDATE SET size = EXCLUDED.size;\n\n")
    
    f.write("COMMIT;\n")

print("de_DE data generated successfully.")
