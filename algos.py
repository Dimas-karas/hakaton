import pandas as pd
import networkx as nx
import numpy as np
from haversine import haversine as dist
from datetime import datetime, timedelta
from tqdm import tqdm
from functools import reduce


def algos():
    with pd.ExcelFile('ГрафДанные.xlsx') as xl:
        points = pd.read_excel(xl, sheet_name='points',
                               index_col=0,
                               usecols=range(4))

        points.longitude = points.longitude.apply(lambda x: x - 360 if x > 180 else x)

        edges = pd.read_excel(xl,
                              sheet_name='edges',
                              index_col=0,
                              usecols=range(4))

        for col in 'start_point_id', 'end_point_id':
            edges[col] = edges[col].map(points.point_name)

    graph = nx.from_pandas_edgelist(df=edges,
                                    source='start_point_id',
                                    target='end_point_id',
                                    edge_attr=True)

    requests = pd.read_excel('Расписание движения судов.xlsx').dropna()


    def get_points_weather():
        weather = pd.ExcelFile('IntegrVelocity.xlsx')

        lon = pd.read_excel(weather,
                            sheet_name='lon',
                            header=None) \
            .values.ravel()

        lon = np.array(tuple(map(lambda x: 180 - x if x > 180 else x, lon)))

        lat = pd.read_excel(weather,
                            sheet_name='lat',
                            header=None) \
            .values.ravel()

        global ice_sheet_names
        ice_sheet_names = weather.sheet_names[2:]

        # Находим какие точки координатной сетки ближе всего к тем, через которые идут маршруты
        closest_dots = np.array([[dist((dot_lat, dot_lon), (lat, lon))
                                  for lat, lon in tuple(zip(lat, lon))]
                                 for dot_lat, dot_lon in tqdm(points[['latitude', 'longitude']].values,
                                                              desc='Looking for closest dots')]).argsort(axis=1)

        # Смотрим, где находится вода, чтобы не строить маршршрут через сушу
        is_water = np.zeros_like(lon)

        ices = []
        for sheet_name in tqdm(ice_sheet_names, desc='Looking for water'):
            ices.append(pd.read_excel(weather,
                                      sheet_name=sheet_name,
                                      header=None) \
                        .values.ravel().round().astype(int))

            is_water += (ices[-1] >= 10)

        is_water = (is_water > 1)

        # Находим точки на координатной сетке, ближайшие к тем, через которые идут маршруты и где есть вода
        new_idxs = []
        for dot in closest_dots:
            for idx in dot:
                if is_water[idx]:
                    new_idxs.append(idx)
                    break

        points.index = pd.Index(data=new_idxs,
                                name=points.index.name)

        # Добавляем ледовую обстановку, соответствующую каждой точке пути на каждую дату
        for sheet_name, data in zip(ice_sheet_names, ices):
            points[sheet_name] = data[points.index]
        return points

    points = get_points_weather()

    points.to_csv('points_weather.csv')

    def get_speed(ice_load, ice_class, clear_speed=0):

        """Возращает скорость движения и возможность самостоятельно движения
        Если скорость 0, то движение запрещено,
        Для ледоколов вместо ice_class нужно сразу писать название судна"""

        ice_class = ice_class.replace(' ', '').lower()

        if ice_class == '50летпобеды':
            if ice_load >= 20:
                return 22, True
            elif ice_load >= 10:
                return ice_load, True

        elif ice_class == 'ямал':
            if ice_load >= 20:
                return 21, True
            elif ice_load >= 10:
                return ice_load, True

        elif ice_class in ('таймыр', 'вайгач'):
            if ice_load >= 20:
                return 18.5, True
            elif ice_load >= 15:
                return ice_load * 0.9, True
            elif ice_load >= 10:
                return ice_load * 0.75, True

        if ice_load >= 20:
            return clear_speed, True
        elif ice_load < 10:
            return 0, False

        if ice_class in ['нет', 'noiceclass'] + [f'ice{x}' for x in range(1, 4)]:
            if ice_load >= 15:
                return clear_speed, False
            else:
                return 0, False

        elif ice_class in [f'arc{x}' for x in range(4, 7)]:
            if ice_load >= 15:
                return clear_speed * 0.8, False
            else:
                return clear_speed * 0.7, False

        elif ice_class == 'arc7':
            if ice_load >= 15:
                return clear_speed * 0.6, True
            else:
                return clear_speed * 0.85, False

    def get_path(request):
        name, ice_class, clear_speed, start, final, date = request

        if start == final:
            return pd.DataFrame({'dot1': start,
                                 'dot2': final,
                                 'speed': 0,
                                 'dot1_time': date,
                                 'dot2_time': date,
                                 'travel_hours': 0,
                                 'wiring': False},
                                index=[0])

        path_dots = nx.shortest_path(graph,
                                     source=start,
                                     target=final,
                                     weight='length')

        path = pd.DataFrame(columns=['dot1', 'dot2', 'speed', 'dot1_time', 'dot2_time', 'travel_hours', 'wiring'],
                            index=pd.MultiIndex.from_arrays([[name] * (len(path_dots) - 1), range(len(path_dots) - 1)],
                                                            names=['name', 'move_id']))

        for i in range(len(path_dots) - 1):

            for ice_date in ice_sheet_names:
                if date <= datetime.strptime(ice_date, '%d-%b-%Y') + timedelta(days=7):
                    break

            ice_load = points.loc[points.point_name.isin(path_dots[i:i + 2]), ice_date].mean()

            speed, singly = get_speed(ice_load=ice_load,
                                      ice_class=ice_class,
                                      clear_speed=clear_speed)

            length = edges[edges.start_point_id.isin(path_dots[i:i + 2]) & edges.end_point_id.isin(path_dots[i:i + 2])][
                'length'].iloc[0]

            if speed:
                path.loc[(name, i)] = [path_dots[i],
                                       path_dots[i + 1],
                                       speed,
                                       date,
                                       date + timedelta(hours=int(length / speed)),
                                       int(length / speed),
                                       not singly]
                date += timedelta(hours=int(length / speed))

            else:
                break

        return path.dropna()

    def get_ideal_timesheet(requests):
        routes = pd.concat(
            [get_path(req).reset_index(level=1, drop=True) for _, req in requests.iterrows()]).sort_values('dot1_time')

        routes.index = pd.MultiIndex.from_tuples([(name, idx) for idx, name in enumerate(routes.index)],
                                                 names=['name', 'move_id'])
        return routes

    routes = get_ideal_timesheet(requests)

    routes.to_csv('ideal_timesheet.csv')

    def get_timesheet(routes):
        global icebreakers
        icebreakers = {'50 лет Победы': 'пролив Лонга',
                       'Ямал': 'Рейд Мурманска',
                       'Таймыр': 'Мыс Желания',
                       'Вайгач': 'Победа месторождение'}

        timesheet = pd.DataFrame(
            columns=['dot1', 'dot2', 'speed', 'on_dot1_time', 'wait_hours', 'dot2_time', 'travel_hours', 'with'],
            index=pd.MultiIndex.from_arrays([icebreakers.keys(), [-1] * 4],
                                            names=['name', 'move_id']))

        timesheet.dot2 = icebreakers.values()
        timesheet.dot2_time = datetime(year=2022, month=2, day=27)

        routes_idxs = routes.index.to_list()

        for idx in tqdm(routes.index, desc='Распределяем ледоколы по заявкам'):
            # Если данный участок ещё не обработан
            if idx in routes_idxs:
                route = routes.loc[idx]
                routes_idxs.remove(idx)
                # Если нужна проводка
                if route.wiring:
                    times_on_place = []
                    # Ищем ледокол, который сможет вовремя приплыть
                    for ib in icebreakers:
                        last_location = timesheet.xs(ib, level=0).iloc[-1]
                        request = pd.Series({'name': ib,
                                             'ice_class': ib,
                                             'clear_speed': 0,
                                             'start': last_location['dot2'],
                                             'final': route['dot1'],
                                             'date': last_location['dot2_time']})
                        times_on_place.append((ib, get_path(request)))
                    times_on_place.sort(key=lambda x: x[1]['dot2_time'].iloc[-1])
                    ib, ib_route = times_on_place[0]
                    if len(ib_route) >= 2 or ib_route.dot1.iloc[0] != ib_route.dot2.iloc[0]:
                        for way_idx, way in ib_route.iterrows():
                            for onway_idx, onway in routes.loc[(routes['dot1'] == way['dot1']) & \
                                                               (routes.dot2 == way.dot2) & (
                                                                       routes.dot1_time <= way.dot1_time) & \
                                                               (routes.wiring == True) & (
                                                               routes.index.isin(routes_idxs))].iterrows():
                                routes_idxs.remove(onway_idx)
                                timesheet.loc[onway_idx, :] = [way.dot1,
                                                               way.dot2,
                                                               way.speed,
                                                               way.dot1_time,
                                                               int((
                                                                               way.dot1_time - onway.dot1_time).total_seconds() / 3600),
                                                               way.dot2_time,
                                                               way.travel_hours,
                                                               ib]

                            timesheet.loc[(ib, 1000 + len(timesheet)), :] = [way.dot1,
                                                                             way.dot2,
                                                                             way.speed,
                                                                             way.dot1_time,
                                                                             0,
                                                                             way.dot2_time,
                                                                             way.travel_hours,
                                                                             '']

                    timesheet.loc[idx, :] = [route.dot1,
                                             route.dot2,
                                             route.speed,
                                             route.dot1_time,
                                             int((timesheet['dot2_time'].xs(ib, level='name').iloc[
                                                      -1] - route.dot1_time).total_seconds() / 3600),
                                             route.dot2_time,
                                             way.travel_hours,
                                             ib]
                    timesheet.loc[(ib, idx[1]), :] = [route.dot1,
                                                      route.dot2,
                                                      route.speed,
                                                      route.dot1_time,
                                                      int((timesheet['dot2_time'].xs(ib, level='name').iloc[
                                                               -1] - route.dot1_time).total_seconds() / 3600),
                                                      route.dot2_time,
                                                      way.travel_hours,
                                                      '']


                else:
                    timesheet.loc[idx, :] = [route.dot1, route.dot2, route.speed, route.dot1_time, 0, route.dot2_time,
                                             route.travel_hours, '']

        return timesheet.dropna()

    timesheet = get_timesheet(routes)

    timesheet.to_csv('timesheet_real.csv')

    def get_work_hours():
        return {ib: timesheet.xs(ib, level='name')['travel_hours'].sum() for ib in icebreakers}

    pd.DataFrame(get_work_hours(), index=[0]).to_csv('ledocol_anal.csv')

    # def compare_timesheets(ideal_ts, real_ts):
    #     return {'percents': 100 * ideal_ts.travel_hours.sum() / (
    #                 ideal_ts.travel_hours.sum() + real_ts.wait_hours.apply(lambda x: max(0, x)).sum()),
    #             'mean_delay_hours': real_ts.wait_hours.apply(lambda x: max(0, x)).sum() / len(requests),
    #             'all_delay_hours': real_ts.wait_hours.apply(lambda x: max(0, x)).sum(),
    #             'mean_way_hours': real_ts.travel_hours.sum() / len(requests)}
    #
    # compare_timesheets(routes, timesheet)

    def get_final_time(timesheet):
        return {name: timesheet.xs(name, level='name').iloc[-1]['dot2_time']
                for name in timesheet.index.get_level_values(level='name').unique()}


    timesheet = pd.DataFrame(get_final_time(timesheet), index=[0])
    timesheet.to_csv('timesheet_time.csv')


with pd.ExcelFile('ГрафДанные.xlsx') as xl:
    points = pd.read_excel(xl, sheet_name='points',
                           index_col=0,
                           usecols=range(4))

    points.longitude = points.longitude.apply(lambda x: x - 360 if x > 180 else x)

    edges = pd.read_excel(xl,
                          sheet_name='edges',
                          index_col=0,
                          usecols=range(4))

    for col in 'start_point_id', 'end_point_id':
        edges[col] = edges[col].map(points.point_name)

graph = nx.from_pandas_edgelist(df=edges,
                                source='start_point_id',
                                target='end_point_id',
                                edge_attr=True)

requests = pd.read_excel('Расписание движения судов.xlsx').dropna()

def get_path_dots(name):
    way = requests[requests['Название судна'] == name]
    return nx.shortest_path(graph,
                            source=way['Пункт начала плавания'].iloc[0],
                            target=way['Пункт окончания плавания'].iloc[0],
                            weight='length')