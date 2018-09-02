from math import pow
import numpy as np
import copy
import sys
import xml.etree.ElementTree as ET

# муравей
class Ant:
    def __init__(self, task):
        self.task = task # текущая вершина-задача, в которой находится муравей
        self.proc = -1 # текущая вершина-процессор, в которой находится муравей
        self.path_to_proc = [] # путь муравья от задачи к процессору
        self.path_to_task = [] # путь муравья от процессора к задаче
        # табу-списки муравья
        self.tl_tasks = [1 for i in range(tasks)]
        self.tl_processors = [1 for i in range(processors)]
        # список времени работы каждого процессора для текущего муравья
        self.time_proc = [0 for i in range(processors)]
        
    def max_proc_time(self):
        return max(self.time_proc)
        
    def clear(self, task):
        self.task = task
        self.proc = -1
        self.path_to_proc.clear()
        self.path_to_task.clear()
        for i in range(tasks):
            self.tl_tasks[i] = 1
        for i in range(processors):
            self.tl_processors[i] = 1
        for i in range(processors):
            self.time_proc[i] = 0

# ребра графа
class Edge:
    def __init__(self, ph=0.05, lf=0):
        self.ph = ph # феромон
        self.lf = lf # локальная целевая функция

# изменение феромона для ребер, выходящих из вершин процессоров
def change_to_task_ph(path): # path - путь как список пар (задача, процессор)
    # какие процессоры участвуют в пути:
    used_pr = set()
    for pr, t in path:
        used_pr.add(pr)
    # обновляем феромон для каждой вершины пути
    c_unused_pr = processors - len(used_pr) # количество неиспользованных процессоров
    for pr, t in path:
        add_ph = 0 # добавочный феромон
        for upr in used_pr: # для каждого использованного процессора в этом пути ...
            add_ph += processor[upr][t].ph # ... добавляем веса ребер, ведущих к заданной вершине
        if c_unused_pr != 0:
            add_ph /= c_unused_pr # значение добавочного феромона тем больше, чем больше процессоров было использовано в пути
        processor[pr][t].ph += add_ph

# изменение феромона для ребер, выходящих из вершин задач
def change_to_proc_ph(path): # path - путь как список пар (процессор, задача)
    for t, pr in path:
        add_ph = 1
        task[t][pr].ph += add_ph

# испарение феромона на каждой итерации
def evaporation_ph(p):
    for i in range(tasks):
        for j in range(processors):
            task[i][j].ph *= (1-p)
    for i in range(processors):
        for j in range(tasks):
            processor[i][j].ph *= (1-p)

# вероятность выбора очередного ребра
def probability(edges, i):
    denom = 0
    for edge in edges:
        denom += pow(edge.ph, alpha) * pow(edge.lf, beta)
    numer = pow(edges[i].ph, alpha) * pow(edges[i].lf, beta)
    if denom:
        return numer/denom
    else:
        return 0

''' # входные данные
processors = eval(input())
tasks = eval(input())
tasks_time = []
for i in range(tasks):
    tasks_time.append(eval(input()))
'''

# входные данные
in_xml = sys.argv[1]

tree = ET.parse(in_xml)
root = tree.getroot()
tasks = eval(root.attrib['number_of_tasks'])
processors = eval(root.attrib['number_of_processors'])
tasks_time = []
for task in root.findall('task'):
    time = eval(task.find('duration_time').text)
    tasks_time.append(time)      
    
# строим граф
task = [] # ребра, выходящие из вершин задач
for i in range(tasks):
    task.append([])
    for j in range(processors):
        task[i].append(Edge(lf=1))
processor = [] # ребра, выходящие из вершин процессоров
for i in range(processors):
    processor.append([])
    for j in range(tasks):
        processor[i].append(Edge(lf=tasks_time[j]))
        
# список муравьев
ants = []
for i in range(tasks): # количество муравьевв берем равным количеству задач
    ants.append(Ant(i))

# !!! сам муравьиный алгоритм !!!
p = 0.05 # коэффициент испарения феромона
alpha = 1.5 # подбираемый коэффициент
beta = 2 # подбираемый коэффициент

# в качестве ответа получаем путь
the_best_path = None

prev_max_proc_time = 0
cur_max_proc_time = 0 # текущее максимальное время работы процессора
for time in tasks_time:
    cur_max_proc_time += time
    
for i in range(1000): # пока этот параметр не перестанет меняться
    for ant in ants:
        while True: # пока не кончатся назначаемые задачи
            
            # выбираем процессор для задачи
            probabilities = [0.0 for i in range(processors)] # список вероятностей для выбора процессора
            if 1 in ant.tl_processors:
                sum_probabilities = 0
                i_probability = -1
                for i in range(processors):
                    if ant.tl_processors[i]:
                        probabilities[i] = probability(task[ant.task], i)
                        sum_probabilities += probabilities[i]
                        i_probability = i
                sum_probabilities -= probabilities[i_probability]
                probabilities[i_probability] = 1 - sum_probabilities
            else:
                print("Error: task exists, but there is no processors for it.")
                exit(1)
            # случайно выбираем процессор в соотвествии с посчитанными вероятностями
            chosen_proc = np.random.choice(processors, p=probabilities)
            
            # обновляем данные муравья
            ant.proc = chosen_proc # на следующем шаге муравей переползет на процессор
            ant.path_to_proc.append((ant.task, ant.proc)) # формируется часть пути "к процессору"
            ant.tl_tasks[ant.task] = 0 # табу-лист задач
            ant.time_proc[ant.proc] += tasks_time[ant.task] # обновляем список времени работы процессоров
            if ant.time_proc[ant.proc] > cur_max_proc_time:
                ant.tl_processors[ant.proc] = 0 # превышено максимальное время работы - процессор отправляется в табу-лист
            ant.task = -1 # уползаем из задачи
            
            # выбираем задачу для процессора
            probabilities = [0.0 for i in range(tasks)] # список вероятностей для выбора задачи
            if 1 in ant.tl_tasks:
                sum_probabilities = 0
                i_probability = -1
                for i in range(tasks):
                    if ant.tl_tasks[i]:
                        probabilities[i] = probability(processor[ant.proc], i)
                        sum_probabilities += probabilities[i]
                        i_probability = i
                sum_probabilities -= probabilities[i_probability]
                probabilities[i_probability] = 1 - sum_probabilities
            else:
                break # больше нет задач в списке
            # случайно выбираем задачу в соотвествии с посчитанными вероятностями
            chosen_task = np.random.choice(tasks, p=probabilities)

            # обновляем данные муравья
            ant.task = chosen_task # на следующем шаге муравей переползет на задачу
            ant.path_to_task.append((ant.proc, ant.task)) # формируется часть пути "к задаче"
            ant.proc = -1 # уползаем с задачи
            
    # для этой итерации - какое лучшее время?        
    prev_max_proc_time = cur_max_proc_time
    the_best_ant = None
    for ant in ants:
        if ant.max_proc_time() < cur_max_proc_time:
            cur_max_proc_time = ant.max_proc_time()
            the_best_ant = ant
    
    # для лучшего муравья - обновляем феромоны на ребрах и записываем путь
    if the_best_ant is not None:
        evaporation_ph(p)
        change_to_task_ph(the_best_ant.path_to_task)
        change_to_proc_ph(the_best_ant.path_to_proc)
        the_best_path = copy.deepcopy(the_best_ant.path_to_proc)
        
    # очищаем память муравья
    for i in range(tasks):
        ants[i].clear(i)

# !!! конец муравьиного алгоритма !!!

# итоговое многопроцессорное расписание (порядок внутри каждого процессора значения не имеет)
schedule = {}
for i in range(processors):
    schedule[i+1] = set()
for t, pr in the_best_path:
    schedule[pr+1].add(t+1)
    
print("Итогововое расписание: " + str(schedule))   
print("Максимальное время работы процессора: " + str(cur_max_proc_time))








            
