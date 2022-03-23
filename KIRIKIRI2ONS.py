import chardet
import glob
import sys
import os
import re

same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
char_dir=os.path.join(same_hierarchy,'char')
scenario_dir = os.path.join(same_hierarchy,'data','scenario')
first_ks = os.path.join(same_hierarchy,'data','script','first.ks')

sel_spnum = 28
sel_sparg = []
effect_list=[]


#--------------------def--------------------
def quodel(s):
	s=str(s).replace('"', '')
	return s


def list2dict(l):
	#半角スペースで命令文を分割し、
	#それらを更に"="で分割("="の先がない場合はTrue)
	#そうしてできた二次元配列を辞書に変換しreturn

	#例:stage=暗転 hideall msgoff trans=normal time=1000
	#  →{'stage': '暗転', 'hideall': True, 'msgoff': True, 'trans': 'normal', 'time': '1000'}
	l2 = []
	for d in l[0][1].split():
		l2 += [d.split('=')] if re.search('=', d) else [[d,True]]

	return dict(l2)


def effect_edit(t,f):
	global effect_list

	list_num=False
	for i, e in enumerate(effect_list,21):#一桁だとprint時番号が競合する可能性あり
		if (e[0] == t) and (e[1] == f):
			list_num = i

	if not list_num:
		effect_list.append([t,f])
		list_num = len(effect_list)+20

	return str(list_num)


def def_kakkoline(line):
	global sel_spnum
	global sel_sparg
	linedef = line

	if kakko_line[0][0] == 'jump':
		line='goto '+quodel(kakko_dict.get('target'))

	if kakko_line[0][0] == 'call':
		line='gosub *'+quodel(kakko_dict.get('storage')).replace('.ks', '_ks')

	elif kakko_line[0][0] == 'name':
		line='mov $1,'+kakko_dict.get('text')

	elif kakko_line[0][0] == 'wait':
		line='wait '+quodel(kakko_dict.get('time'))

	elif kakko_line[0][0] == 'bgm':
		line='bgm "bgm\\'+ quodel(kakko_dict.get('file')) +'.ogg"'

	elif kakko_line[0][0] == 'se':
		cv_path = os.path.join(same_hierarchy, 'cv', quodel(kakko_dict.get('file'))+'.ogg')
		se_path = os.path.join(same_hierarchy, 'se', quodel(kakko_dict.get('file'))+'.ogg')

		if os.path.isfile(cv_path):
			path_dir = 'cv'

		elif os.path.isfile(se_path):
			path_dir = 'se'
		
		else:
			path_dir = ''

		line='dwave 1,"'+path_dir+'\\'+quodel(kakko_dict.get('file'))+'.ogg"' if path_dir else ';dwave 1,"convert_error.ogg"'

	elif kakko_line[0][0] == 'voice':
		line='dwave 0,"cv\\'+quodel(kakko_dict.get('file'))+'.ogg"'

	elif kakko_line[0][0] == 'haikei':
		if kakko_dict.get('file') == '"black"' or kakko_dict.get('file') == '"white"':
			path_rel = quodel(kakko_dict.get('file'))

		else:
			eve_path = os.path.join(same_hierarchy, 'evecg', quodel(kakko_dict.get('file'))+'.png')
			sys_path = os.path.join(same_hierarchy, 'syscg', quodel(kakko_dict.get('file'))+'.png')

			if os.path.isfile(eve_path):
				path_dir = 'evecg'

			elif os.path.isfile(sys_path):
				path_dir = 'syscg'
		
			path_rel = '"'+path_dir+'\\'+quodel(kakko_dict.get('file'))+'.png"'

		line = 'csp 5:bg '+path_rel+','+effect_edit(kakko_dict.get('time'), kakko_dict.get('fade'))

	elif kakko_line[0][0] == 'char_c':
		line='lsp 11,"evecg\\'+quodel(kakko_dict.get('file'))+'.png",0,0'		

	elif kakko_line[0][0] == 'char_action':
		line='print '+effect_edit(kakko_dict.get('time'), '"cross"')#print命令はクロスフェードのため吉里吉里側"cross"命令に偽装

	elif kakko_line[0][0] == 'crossfade':
		line='print '+effect_edit(kakko_dict.get('time'), '"cross"')#print命令はクロスフェードのため吉里吉里側"cross"命令に偽装

	elif kakko_line[0][0] == 'stop_bgm':
		line='bgmstopfadeout '+(quodel(kakko_dict.get('fadeout')))

	elif kakko_line[0][0] == 'stop_se':
		line='sestopfadeout '+(quodel(kakko_dict.get('fadeout')))

	elif kakko_line[0][0] == 'exbutton':
		btn_x=(quodel(kakko_dict.get('x')))
		btn_y=(quodel(kakko_dict.get('y')))
		btn_file=(quodel(kakko_dict.get('file')))
		sel_sparg.append(re.findall(r'"ChJump\(\'\', \'\*([A-z0-9_]+)\'\)"', line)[0])
		line='lsp '+str(sel_spnum)+',":a/3,0,3;syscg\\'+btn_file+'.png",'+btn_x+','+btn_y
		sel_spnum += 1

	#無変更時コメントアウト/変更時末尾に改行挿入
	line = r';' + line if linedef == line else line + '\n'
	return line


#--------------------event--------------------
add0txt_effect = 'エフェクト定義 - 2\n'

with open(first_ks, encoding='utf-16', errors='ignore') as f:
	txt_f = f.read()
	add0txt_title = re.search(r'\[title name="(.+?)(　Ver.\...)?"\]', txt_f).group(1)

with open(os.path.join(same_hierarchy, 'default.txt')) as f:
	txt = f.read()

for ks_path in glob.glob(os.path.join(scenario_dir, '*')):
	
	with open(ks_path, 'rb') as f:
		char_code =chardet.detect(f.read())['encoding']

	with open(ks_path, encoding=char_code, errors='ignore') as f:
		#ks名をそのままonsのgoto先のラベルとして使い回す
		txt += '\n\n*' + os.path.splitext(os.path.basename(ks_path))[0] + '_ks\n'

		for line in f:

			#最初にやっとくこと
			kakko_line = re.findall(r'\[(jump|call|name|wait|bgm|se|voice|haikei|char_c|char_action|crossfade|stop_bgm|stop_se|exbutton) (.+?)\]',line)#括弧行定義
			line = re.sub(r'\[ruby text="(.+?)" align="."\]\[ch text="(.+?)"\]', r'(\2/\1)', line)#ルビ置換

			if re.search('^\n', line):#空行
				#line = ''
				pass#そのまま放置

			elif re.search(';', line):#元々のメモ
				line = line.replace(';', ';;;;;')#分かりやすく

			elif re.search(r'\[tp\]', line):
				line = 'gosub *tp\n'

			elif re.search(r'\[hide_char\]', line):
				line = 'csp 11\n'

			elif re.search(r'\[stop_se\]', line):
				line = 'dwavestop 0\n'

			elif re.search(r'\[return\]', line):
				line = 'return\n'

			elif re.search(r'\[begin_link\]', line):#選択肢はじめ
				sel_spnum = 28
				sel_sparg = []
				line = r';' + line#エラー防止の為コメントアウト

			elif re.search(r'\[end_link\]', line):#選択肢おわり
				line = 'gosub *select_mode\n'
				for i,a in enumerate(sel_sparg,8):#28のボタン番号→8
					line += 'if %3='+str(i)+' goto *'+a+'\n'

			elif re.search(r'\*[A-z0-9_]+\|', line):
				line = line.replace('|', '')

			elif not re.search('[A-z]', line):#半角英字が存在しない(≒表示する文字)
				line = 'mov $0,"' + line.replace('\n', '"\n')#行末に

			elif kakko_line:#[]で呼び出し
				kakko_dict = list2dict(kakko_line)
				line = def_kakkoline(line)

			else:#どれにも当てはまらない、よく分からない場合
				line = r';' + line#エラー防止の為コメントアウト

			txt += line

for i,e in enumerate(effect_list,21):#エフェクト定義用の配列を命令文に&置換

	if e[1] == '"cross"':
		add0txt_effect +='effect '+str(i)+',10,'+quodel(e[0])+'\n'

	else:
		add0txt_effect +='effect '+str(i)+',18,'+quodel(e[0])+',"data\\rule\\rule'+quodel(e[1])+'.png"\n'

txt = txt.replace(r'<<-TITLE->>', add0txt_title)
txt = txt.replace(r'<<-EFFECT->>', add0txt_effect)

#作品個別処理
if add0txt_title[0]=='曾':#138
	txt = txt.replace(r';<<-BRANDCALL->>', r'dwave 1,"cv\brandcall.ogg"')
	txt = txt.replace(r';<<-TITLECALL->>', r'dwave 1,"cv\titlecall.ogg"')
	txt = txt.replace(r'goto *GameEnd', r'goto *title')#終了後タイトルに戻る
	txt = txt.replace(r'goto *b05_000', r'select "ＧＯＯＤＥＮＤへ",*c05_000,"ＢＡＤＥＮＤへ",*b05_000')#選択分岐処理実装面倒だったので

	end_pic = 6000
	end_snd = 97

elif add0txt_title[:2]=='まご':#173
	txt = txt.replace(r';<<-BRANDCALL->>', r'dwave 1,"cv\brandcall00.ogg"')
	txt = txt.replace(r';<<-TITLECALL->>', r'dwave 1,"cv\titlecall00.ogg"')
	txt = txt.replace(r'goto *Gamebad', r'goto *title')#終了後タイトルに戻る
	txt = txt.replace(r';<<-ALL_WINDOW_MODE->>', r'mov $3,"A"')#キャラ名の有無でのウィンドウ変更を無効化

	end_pic = 6700
	end_snd = 106

else:
	txt = False


if txt:


	#低スペック機での動作を見据え、スクロール時のフレーム数を1/10程度にしてます
	txt = txt.replace(r'bgm "bgm\bgmed01.ogg"', 'dwave 2,"bgm\\bgmed01.ogg"\nsaveoff:csp 5:btndef "syscg\\staff.png"\nfor %5=0 to '+str(int(end_pic/10))+'\nblt 0,0,800,600,0,0+%5*10,800,600:wait '+str(int(end_snd/end_pic*10000))+'\nnext\nofscpy:click\ndwavestop 2:return\n')
	
	open(os.path.join(same_hierarchy,'0.txt'), 'w', errors='ignore').write(txt)
