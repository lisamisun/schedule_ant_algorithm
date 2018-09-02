import xml.etree.ElementTree as ET
import random
import sys

max_duration = 50

processors = eval(sys.argv[1])
tasks = eval(sys.argv[2])
test_file = sys.argv[3]

tree = ET.ElementTree()
root = ET.Element("want_schedule", {"number_of_tasks":str(tasks), "number_of_processors":str(processors)})
tree._setroot(root)

random.seed()
for i in range(tasks):
    task = ET.Element("task", {"task_number":str(i+1)})
    time_of_task = ET.SubElement(task, "duration_time")
    time_of_task.text = str(random.randint(1, max_duration))
    root.append(task)

tree.write(test_file)
