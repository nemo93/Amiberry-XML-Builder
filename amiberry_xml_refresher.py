import sys
import os
from pathlib import Path
import math
import datetime
from utils import text_utils
import shutil
from lxml import etree

# =======================================
# Methods
# =======================================
# Get a value from a file
def value_list(in_file, game_name):
    file_name = 'settings/' + in_file

    if os.path.isfile(file_name) is False:
        return ''

    with open(file_name) as f:
        content = f.readlines()
        content = [x.strip() for x in content]
    f.close()

    answer = ''

    for this_line in content:
        if not this_line == '':
            this_word = this_line.split()
            if this_word[0] == game_name:
                answer = this_word[1]
                break

    return answer

# Ensure a game package is set within a file
def check_list(in_file, game_name):
    temp_game = game_name
    file_name = 'settings/' + in_file

    if os.path.isfile(file_name) is False:
        return False

    with open(file_name) as f:
        content = f.readlines()
        content = [x.strip() for x in content]
    f.close()

    answer = False

    for this_line in content:
        if this_line == temp_game:
            answer = True
            break

    return answer

# For XML sorting
def sortchildrenby(parent, attr):
    parent[:] = sorted(parent, key=lambda child: child.get(attr))

# =======================================
# main section starting here...
# =======================================
script_version = '0.9'
print()
print(
    text_utils.FontColours.BOLD + text_utils.FontColours.OKBLUE + "HoraceAndTheSpider and osvaldolove's" + text_utils.FontColours.ENDC + text_utils.FontColours.BOLD +
    " Amiberry XML Refresher" + text_utils.FontColours.ENDC + text_utils.FontColours.OKGREEN + " ("+script_version+")" + text_utils.FontColours.ENDC)
print()

whdbfile = 'whdload_db.xml'
whdbtmp = 'whdload_db.xml.tmp'
whdbbak = 'whdload_db.xml.bak'

# also get whdbfile size before modification
whdsize = Path(whdbfile).stat().st_size

# =======================================
# Backup before doing naughty stuff!!
# =======================================
if not os.path.isfile(whdbbak) or whdsize >= os.stat(whdbbak).st_size:
    shutil.copy2(whdbfile, whdbbak)
    whdbaksize = Path(whdbbak).stat().st_size

# Start to format XML and extract some values
XML_HEADER = '<whdbooter timestamp="' + datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S") + '">' + chr(10)
XML = ''
XML_FOOTER = '</whdbooter>'

# brutal way: extract and reinject data into the XML.
# need to think of a smarter to do that // perf.
root = etree.parse(whdbfile).getroot()
total_item = len(root.getchildren()) 
count = 0

for item in root.findall('game'):
    count += 1
    file_name = item.xpath('@filename')[0]
    ArchiveSHA = item.xpath('@sha1')[0]

    full_game_name = item.find('name').text
    sub_path = item.find('subpath').text
    variant_uuid = item.find('variant_uuid').text
    slave_count = item.find('slave_count').text
    slave_default = item.find('slave_default').text
    slave_libraries = item.find('slave_libraries').text
    # Extract the 'slave' block
    SLAVE_XML = ''
    SXML = []
    for slave in item.findall('.slave'):
      SXML.append(etree.tostring(slave).decode()) # convert to str
      SLAVE_XML = ''.join(SXML)

    # Get FAST_RAM if already set / max FAST_RAM 8Mb
    hw_fast_ram = item.find('hardware').text
    if hw_fast_ram.find('FAST_RAM=8') > -1:
      hw_fast_ram = 8

    # Attempt to fix empty name or subpath
    if not full_game_name or not sub_path:
      full_game_name = file_name.replace('_',' ')
      get_sub_path = text_utils.left(slave_default,len(slave_default) - len('.slave'))
      if get_sub_path.find('\\') > -1:
        sub_path = get_sub_path.split('\\', 1)[0]
      else:
        sub_path = get_sub_path
                
    # '======== DISPLAY SETTINGS =======
    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # ' screen heights { 200, 216, 224, 240, 256, 262, 270 };
    HW_HEIGHT = ''
    if check_list('Screen_Height_270.txt', sub_path) is True:
      HW_HEIGHT = '270'
    if check_list('Screen_Height_262.txt', sub_path) is True:
      HW_HEIGHT = '262'
    if check_list('Screen_Height_256.txt', sub_path) is True:
      HW_HEIGHT = '256'
    if check_list('Screen_Height_240.txt', sub_path) is True:
      HW_HEIGHT = '240'
    if check_list('Screen_Height_224.txt', sub_path) is True:
      HW_HEIGHT = '224'
    if check_list('Screen_Height_216.txt', sub_path) is True:
      HW_HEIGHT = '216'
    if check_list('Screen_Height_200.txt', sub_path) is True:
      HW_HEIGHT = '200'

    # ' screen widths  { 320, 352, 384, 640, 704, 768 };
    HW_WIDTH = ''
    if check_list('Screen_Width_320.txt', sub_path) is True:
      HW_WIDTH = '320'
    if check_list('Screen_Width_352.txt', sub_path) is True:
      HW_WIDTH = '352'
    if check_list('Screen_Width_384.txt', sub_path) is True:
      HW_WIDTH = '384'
    if check_list('Screen_Width_640.txt', sub_path) is True:
      HW_WIDTH = '640'
    if check_list('Screen_Width_704.txt', sub_path) is True:
      HW_WIDTH = '704'
    if check_list('Screen_Width_768.txt', sub_path) is True:
      HW_WIDTH = '768'
                                
    # ' screen centering (recently added)
    HW_H_CENTER = 'SMART'
    if check_list('Screen_Center_H.txt', sub_path) is True:
      HW_H_CENTER = 'NONE'

    HW_V_CENTER = 'SMART'
    if check_list('Screen_Center_V.txt', sub_path) is True:
      HW_V_CENTER = 'NONE'

    # ' extras
    HW_NTSC = ''
    if check_list('Screen_ForceNTSC.txt', sub_path) is True:
      HW_NTSC = 'TRUE'       
    elif full_game_name.find('NTSC') > -1:
      HW_NTSC = 'TRUE' 
                            
    # '======== CONTROL SETTINGS =======
    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ' mouse / mouse 2 / CD32

    use_mouse1 = check_list('Control_Port0_Mouse.txt', sub_path)
    use_mouse2 = check_list('Control_Port1_Mouse.txt', sub_path)
    use_cd32_pad = check_list('Control_CD32.txt', sub_path)

    chip_ram = 2
    fast_ram = 4
                
    old_chip_ram = chip_ram
    for i in range(0, 4): # No more than 8MB
      chip_ram = int(math.pow(2, i)) / 2
      if chip_ram >= 1:
        chip_ram = int(chip_ram)

      if check_list('Memory_ChipRam_' + str(chip_ram) + '.txt', sub_path) is True:
        chip_ram = int(chip_ram * 2)
        break
     #chip_ram = old_chip_ram
      else:
        chip_ram = old_chip_ram

    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ' when we want different fast ram!!

    old_fast_ram = fast_ram
    for i in range(0, 5): # No more than 16MB
      fast_ram = int(math.pow(2, i))
      if check_list('Memory_FastRam_' + str(fast_ram) + '.txt', sub_path) is True:
        break
     #fast_ram = old_fast_ram
      else:
        fast_ram = old_fast_ram
    
    if hw_fast_ram == 8:
      fast_ram = hw_fast_ram

    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ' when we want different Z3 ram!!

    for i in range(0, 8): # No more than 128MB
      z3_ram = int(math.pow(2, i))
      if check_list('Memory_Z3Ram_' + str(z3_ram) + '.txt', sub_path) is True:
        break
     #z3_ram = 0
      else:
        z3_ram = 0

#    if z3_ram != 0 or fast_ram >= 8:
#      print(sub_path,'-> Z3:',z3_ram,'Fast:',fast_ram,'Chip:',chip_ram)

    # '======== CHIPSET SETTINGS =======
    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ' sprite collisions

    HW_SPRITES = ''
    if check_list('Chipset_CollisionLevel_playfields.txt', sub_path) is True:
      HW_SPRITES = 'PLAYFIELDS'
    if check_list('Chipset_CollisionLevel_none.txt', sub_path) is True:
      HW_SPRITES = 'NONE'
    if check_list('Chipset_CollisionLevel_sprites.txt', sub_path) is True:
      HW_SPRITES = 'SPRITES'
    if check_list('HW_SPRITES.txt', sub_path) is True:
      HW_SPRITES = 'FULL'

    # ' blitter    
    HW_BLITS = ''        
    if check_list('Chipset_ImmediateBlitter.txt', sub_path) is True:
      HW_BLITS = 'IMMEDIATE'
    if  check_list('Chipset_NormalBlitter.txt', sub_path) is True:
      HW_BLITS = 'NORMAL'
    if  check_list('Chipset_WaitBlitter.txt', sub_path) is True:
      HW_BLITS = 'WAIT'

    HW_FASTCOPPER = ''
    if not check_list('Chipset_NoFastCopper.txt', sub_path) is False:
      HW_FASTCOPPER = 'FALSE'

    if check_list('Chipset_FastCopper.txt', sub_path) is True:
      HW_FASTCOPPER = 'TRUE'

    # '======== CPU SETTINGS =======
    # ' ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # ' max emu speed
    HW_SPEED = ''
    if check_list('CPU_MaxSpeed.txt', sub_path) is True:
      HW_SPEED = 'MAX'
    if check_list('CPU_RealSpeed.txt', sub_path) is True:
      HW_SPEED = 'REAL'

    # ' clock speed
    if check_list('CPU_ClockSpeed_7.txt', sub_path) is True:
      HW_SPEED = '7'
    if check_list('CPU_ClockSpeed_14.txt', sub_path) is True:
      HW_SPEED = '14'
    if check_list('CPU_ClockSpeed_28.txt', sub_path) is True:
      HW_SPEED = '28'

    HW_CPU = ''
    # ' cpu model 68000
    if check_list('CPU_68000.txt', sub_path) is True:
      HW_CPU = '68000'
                                
    # ' cpu model 68010
    if check_list('CPU_68010.txt', sub_path) is True:
      HW_CPU = '68010'
      HW_24BIT = 'FALSE'
                                
    # ' cpu model 68040
    if check_list('CPU_68040.txt', sub_path) is True:
      HW_CPU = '68040'
      HW_24BIT = 'FALSE'

    # ' 24 bit addressing 
    HW_24BIT = ''
    if not check_list('CPU_No24BitAddress.txt', sub_path) is False:
      HW_24BIT = 'FALSE'
             
    #   compatible CPU 
    HW_CPUCOMP = ''
    if check_list('CPU_Compatible.txt', sub_path) is True:
      HW_CPUCOMP = 'TRUE'
                    
    #   cycle_exact = check_list('CPU_CycleExact.txt', sub_path)

    #JIT Cache
    HW_JIT = ''
    if check_list('CPU_ForceJIT.txt',sub_path) == True:
      HW_JIT = 'TRUE'
      HW_SPEED = 'MAX'
    elif check_list('CPU_NoJIT.txt', sub_path) == True:
      HW_JIT = 'FALSE'

    # CHIPSET
    HW_CHIPSET = ''
    if check_list('CPU_ForceAGA.txt',sub_path) == True:
      HW_CHIPSET = 'AGA'
    elif check_list('CPU_ForceECS.txt', sub_path) == True:
      HW_CHIPSET = 'ECS'  
    elif check_list('CPU_ForceOCS.txt', sub_path) == True:
      HW_CHIPSET = 'OCS'  

    if file_name.find('_AGA') > -1:
      HW_CHIPSET = 'AGA'                                       
    if file_name.find('_CD32') > -1:
      HW_CHIPSET = 'AGA'
      use_cd32_pad = True


    # ================================
    # building the hardware section
    hardware = ''
    if HW_BLITS != '':
      hardware += ('BLITTER=') + HW_BLITS + chr(10)

    if HW_SPEED != '':
      hardware += ('CLOCK=') + HW_SPEED + chr(10)

    if chip_ram != 2:
      hardware += ('CHIP_RAM=') + str(chip_ram) + chr(10)

    if HW_CHIPSET != '':
      hardware += ('CHIPSET=') + HW_CHIPSET + chr(10)
                    
    if HW_CPU != '':
      hardware += ('CPU=') + HW_CPU + chr(10)
                
    if HW_24BIT != '':
      hardware += ('CPU_24BITADDRESSING=') + HW_24BIT + chr(10)

    if HW_CPUCOMP != '':
      hardware += ('CPU_COMPATIBLE=') + HW_CPUCOMP + chr(10)

    if HW_FASTCOPPER != '':
      hardware += ('FAST_COPPER=') + HW_FASTCOPPER + chr(10)

    if fast_ram != 4:
      hardware += ('FAST_RAM=') + str(fast_ram) + chr(10)

    if HW_JIT != '':
      hardware += ('JIT=') + HW_JIT + chr(10)

    if HW_NTSC != '':
      hardware += ('NTSC=') + HW_NTSC + chr(10)

    if use_mouse1 == True:
      hardware += ('PRIMARY_CONTROL=MOUSE') + chr(10)
    else:
      hardware += ('PRIMARY_CONTROL=JOYSTICK')  + chr(10)       

    if use_mouse1 == True:
      hardware += ('PORT0=MOUSE') + chr(10)
    elif use_cd32_pad == True:
      hardware += ('PORT0=CD32') + chr(10)
    else:
      hardware += ('PORT0=JOY')  + chr(10)       

    if use_mouse2 == True:
      hardware += ('PORT1=MOUSE') + chr(10)
    elif use_cd32_pad == True:
      hardware += ('PORT1=CD32')  + chr(10)       
    else:
      hardware += ('PORT1=JOY')  + chr(10)      

    # SCREEN OPTIONS
    if HW_H_CENTER != '':
      hardware += ('SCREEN_CENTERH=') + HW_H_CENTER + chr(10)

    if HW_V_CENTER != '':
      hardware += ('SCREEN_CENTERV=') + HW_V_CENTER + chr(10)

    if HW_HEIGHT != '':
      hardware += ('SCREEN_HEIGHT=') + HW_HEIGHT + chr(10)

    if HW_WIDTH != '':
      hardware += ('SCREEN_WIDTH') + HW_WIDTH + chr(10)

    if HW_SPRITES != '':
      hardware += ('SPRITES=') + HW_CPU + chr(10)
                    
    if z3_ram != 0:
      hardware += ('Z3_RAM=') + str(z3_ram) + chr(10)

    # custom controls
    custom_file = 'customcontrols/' + full_game_name + '.controls'
    custom_text = ''
                                
    if os.path.isfile(custom_file) == True:
      # remove any items which are not amiberry custom settings
      with open(custom_file) as f:
        content = f.readlines()
        f.close()
                                    
      for this_line in content:
        if this_line.find('amiberry_custom') > -1:
          custom_text += this_line

    extra_libs = 'False'
    if check_list('WHD_Libraries.txt', sub_path) is True:
      extra_libs = 'True'

    ##generate XML
    XML = XML + chr(9) + '<game filename="' + file_name.replace('&', '&amp;') + '" sha1="' + ArchiveSHA + '">' + chr(10)
    XML = XML + chr(9) + chr(9) + '<name>' + full_game_name.replace('&', '&amp;') + '</name>' + chr(10)
    XML = XML + chr(9) + chr(9) + '<subpath>' + sub_path.replace('&', '&amp;') + '</subpath>' + chr(10)
    XML = XML + chr(9) + chr(9) + '<variant_uuid>' + variant_uuid + '</variant_uuid>' + chr(10)
    XML = XML + chr(9) + chr(9) + '<slave_count>' + slave_count + '</slave_count>' + chr(10)
    XML = XML + chr(9) + chr(9) + '<slave_default>' + slave_default.replace('&', '&amp;') + '</slave_default>' + chr(10)
    XML = XML + chr(9) + chr(9) + '<slave_libraries>' + extra_libs  + '</slave_libraries>' + chr(10)
    XML = XML + chr(9)  + chr(9) +  SLAVE_XML
#    XML = XML + SLAVE_XML
#    XML = XML + chr(9)  + chr(9) + '<hardware>'
    XML = XML + '<hardware>'
    XML = XML + chr(10) + chr(9) + chr(9) + hardware.replace(chr(10), chr(10) + chr(9) + chr(9) )
    XML = XML + chr(10) + chr(9) + chr(9) + '</hardware>' + chr(10)

    if len(custom_text)>0:
      XML = XML + chr(9)+ chr(9) + '<custom_controls>' + chr(10) + chr(9) + chr(9) + custom_text  + chr(10) + chr(9) + chr(9) + '</custom_controls>' + chr(10)
                
    XML = XML + chr(9) + '</game>' + chr(10)

    # Showing progress on the command-line
    print('Refreshing XML.',count,'out of',total_item, end='\r', flush=True)


# =======================================
# XML is complete, let's put it all together
# =======================================
XML = XML_HEADER + XML + XML_FOOTER

# =======================================
# print XML and other files
# =======================================
print('Generating XML File')
text_file = open(whdbtmp, 'w+')
text_file.write(XML)
text_file.close()

######
# Should be removed at some point
# Ensure there's no more offsetX/Y related lines
offtext = ['SCREEN_X_OFFSET=', 'SCREEN_Y_OFFSET=', '\t\t\n']

with open(whdbtmp, 'r') as nomoreoffset:
    olines = nomoreoffset.readlines()

with open(whdbtmp, 'w') as nomoreoffset:
    for line in olines:
        if not any(offset in line for offset in offtext):
          nomoreoffset.write(line)
#
######

# Sorting elements / not required but easier to debug
print('Sorting XML File')

tree = etree.parse(whdbtmp)
parent = tree.getroot()
sortchildrenby(parent, 'filename')
tree.write(whdbfile, encoding='utf-8', xml_declaration=True)

# =======================================
# Cleaning
# =======================================
# Remove the tmp whdload_db.xml
os.remove(whdbtmp)

# Note: could use md5 hash instead
# get whdbfile size after modification
whdsize_after = Path(whdbfile).stat().st_size

if whdsize_after > 0 and whdsize_after >= whdsize:
    os.remove(whdbbak)

# =======================================
print('Bye!')
