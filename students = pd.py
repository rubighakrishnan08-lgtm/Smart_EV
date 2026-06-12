import pandas as pd # type: ignore
students = pd.DataFrame({
   'name': ['Alice', 'Bob', 'Charlie', 'Alice', 'Bob', 'Charlie'],
   'subject': ['Math', 'Math', 'Math', 'Science', 'Science', 'Science'],
   'score': [95, 78, 88, 92, 85, 90]
})
print(students)