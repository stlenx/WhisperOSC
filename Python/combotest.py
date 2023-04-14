import PySimpleGUI as psg
names = []
lst = psg.Combo(names, font=('Arial Bold', 14),  expand_x=True, enable_events=True,  readonly=False, key='-COMBO-')
layout = [[lst,
   psg.Button('Add', ),
   psg.Button('Remove'),
   psg.Button('Exit')],
   [psg.Text("", key='-MSG-',
      font=('Arial Bold', 14),
      justification='center')]
   ]
window = psg.Window('Combobox Example', layout, size=(715, 200))
while True:
   event, values = window.read()
   print(event, values)
   if event in (psg.WIN_CLOSED, 'Exit'):
      break
   if event == 'Add':
      names.append(values['-COMBO-'])
      print(names)
      window['-COMBO-'].update(values=names, value=values['-COMBO-'])
      msg = "A new item added : {}".format(values['-COMBO-'])
      window['-MSG-'].update(msg)
   if event == '-COMBO-':
      ch = psg.popup_yes_no("Do you want to Continue?", title="YesNo")
   if ch == 'Yes':
      val = values['-COMBO-']
      names.remove(val)
   window['-COMBO-'].update(values=names, value=' ')
   msg = "A new item removed : {}".format(val)
   window['-MSG-'].update(msg)
window.close()