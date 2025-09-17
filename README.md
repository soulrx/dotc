# DOTC 🎯

**Access nested Python data structures using simple dot notation**

Transform complex nested dictionaries and lists into easily navigable objects with dot notation access.

## Quick Start

```bash
pip install dotc
```

```python
from dotc import Dotc

# Your nested data
data = {
    'user': {
        'name': 'Alice',
        'scores': [85, 92, 78]
    }
}

# Convert to dot-accessible object
d = Dotc(data)

# Access with simple dots
print(d.user.name)      # Alice
print(d.user.scores._0) # 85
```

## ✨ Core Features

### 🔍 Simple Dot Access
Access nested data structures naturally:

```python
data = {'a': 1, 'b': {'c': 3, 'd': [4, 5, 6]}}
d = Dotc(data)

d.a           # Returns: 1
d.b.c         # Returns: 3
d.b.d._0      # Returns: 4 (list access with _index)
```

### 🚀 Instant Results with Spawn
Get both the object and a specific value in one call:

```python
# Get object and value simultaneously
staff_data = {
    'staff': {
        'coders': ['mike', 'jeremie', 'trey', 'donnie']
    }
}

# Method 1: During instantiation with _pathget
dc, result = Dotc(staff_data, _pathget='staff.coders.0')
print(result)  # mike

# Method 2: Using spawn method
dc = Dotc(staff_data)
dc, result = dc.spawn('staff.coders.1')
print(result)  # jeremie

# Method 3: Using factory method
dc, result = Dotc.create_with_result(staff_data, 'staff.coders.2')
print(result)  # trey
```

### 🎯 Programmatic Path Access with `__call__`
Use the call method to get values by path after instantiation:

```python
staff_data = {
    'staff': {
        'coders': ['mike', 'jeremie', 'trey', 'donnie']
    }
}

# Create with initial path extraction
dc, result = Dotc(staff_data, _pathget='staff.coders.0')
print(result)  # mike

# Then use __call__ for additional path queries
result2 = dc('staff.coders.1')  # jeremie
result3 = dc('staff.coders.3')  # donnie
```

### 🛡️ Safe Access with Defaults
Never worry about missing keys:

```python
d = Dotc({'a': {'b': 1}})

d.a.b         # Returns: 1
d.a.missing   # Returns: None (default)
d.x.y.z       # Returns: None (safe traversal)
```

### 🔄 Full Data Resolution
Get the complete resolved data structure:

```python
d = Dotc({'a': 1, 'b': {'c': [2, 3]}})

d._           # Returns: {'a': 1, 'b': {'c': [2, 3]}}
d.b._         # Returns: {'c': [2, 3]}
d.b.c._       # Returns: [2, 3]
```

## 📖 Tutorial

### Basic Usage

```python
from dotc import Dotc

# Simple dictionary
data = {'name': 'John', 'age': 30}
d = Dotc(data)
print(d.name)  # John
print(d.age)   # 30
```

### Nested Dictionaries

```python
data = {
    'person': {
        'details': {
            'name': 'Jane',
            'location': 'NYC'
        }
    }
}

d = Dotc(data)
print(d.person.details.name)      # Jane
print(d.person.details.location)  # NYC
```

### Working with Lists

```python
data = {
    'fruits': ['apple', 'banana', 'cherry'],
    'numbers': [1, 2, 3, 4, 5]
}

d = Dotc(data)
print(d.fruits._0)    # apple
print(d.fruits._1)    # banana
print(d.numbers._4)   # 5
```

### Mixed Nested Structures

```python
data = {
    'users': [
        {'name': 'Alice', 'scores': [95, 87]},
        {'name': 'Bob', 'scores': [78, 92]}
    ]
}

d = Dotc(data)
print(d.users._0.name)        # Alice
print(d.users._0.scores._0)   # 95
print(d.users._1.scores._1)   # 92
```

## 🎯 Advanced Features

### Inspection and Debugging

```python
d = Dotc({'a': 1, 'b': {'c': [1, 2, 3]}})

# Basic inspection
d._show()

# Verbose inspection
d._show(v=1)

# Inspect specific parts
d._show(d.b, v=1)
```

### Using DataPath for Programmatic Access

For cases where you need programmatic path traversal:

```python
from dotc import DataPath

data = {'a': {'b': [1, 2, 3]}}
d = Dotc(data)

dp = DataPath()
result = dp.get('a.b.0', d)  # Returns: 1

# Works with regular Python objects too
result = dp.get('a.b.0', data)  # Returns: 1
```

## 🔧 Configuration Options

```python
d = Dotc(
    data={'a': 1},
    node='custom_name',      # Custom node name
    default='N/A',           # Custom default value
    _strict=1,              # Raise errors for missing keys
    _debug=1                # Enable debug output
)
```

## 🎪 Use Cases

### Configuration Management
```python
config = {
    'database': {'host': 'localhost', 'port': 5432},
    'api': {'timeout': 30, 'retries': 3}
}

cfg = Dotc(config)
db_host = cfg.database.host      # localhost
api_timeout = cfg.api.timeout    # 30
```

### JSON API Response Handling
```python
api_response = {
    'data': {
        'user': {'id': 123, 'profile': {'email': 'user@example.com'}}
    }
}

resp = Dotc(api_response)
email = resp.data.user.profile.email  # user@example.com
```

### Data Processing Pipelines
```python
# Get object and extract value in one step
staff_data = {
    'staff': {
        'coders': ['mike', 'jeremie', 'trey', 'donnie'],
        'metrics': {'team_size': 4, 'experience': 'senior'}
    }
}

# Extract initial value and setup for more queries
processor, first_coder = Dotc.create_with_result(staff_data, 'staff.coders.0')
print(f"Lead developer: {first_coder}")  # Lead developer: mike

# Use the same object for additional queries
team_size = processor('staff.metrics.team_size')
print(f"Team size: {team_size}")  # Team size: 4
```

## 📚 API Reference

### Class Methods
- `Dotc(data, node=None, default=None, **kwargs)` - Create a new Dotc object
- `Dotc.create_with_result(data, pathget, **kwargs)` - Create and extract value simultaneously

### Instance Methods  
- `obj.spawn(pathget)` - Returns `(self, result)` tuple
- `obj(path)` - Get value at path programmatically
- `obj._` - Get fully resolved data structure
- `obj._show(verbosity=0)` - Inspect object structure

### Utility Classes
- `DataPath.get(path, obj, default)` - Static path traversal

---

**DOTC** - Making nested data navigation as easy as ABC! 🎯
