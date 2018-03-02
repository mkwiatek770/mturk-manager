import boto3
from mturk_manager.models import *
from viewer.models import *
from django.urls import reverse
# from secrets import token_urlsafe
from django.conf import settings as settings_django
import uuid
from django.contrib import messages
import re
from collections import Counter

glob_url_sandbox = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'

def get_url_block_worker(request):
    url = None
    try:
        url = settings_django.URL_BLOCK_WORKERS
    except AttributeError:
        url = request.get_host()

    if url.startswith('http'):
        url = url.replace('http://', 'https://')
    else:
        url = 'https://' + url

    return url

def count_parameters_in_template(string_template):
    list_matches = re.findall('\$\{([a-zA-Z0-9_-]+)\}', string_template)
    counter = Counter(list_matches)
    return counter

def is_project_up_to_date(request, db_obj_project, name_project):
    if db_obj_project.version < settings_django.VERSION_PROJECT:
        messages.error(request, 'Project "{}" is not up to date. Go to "settings" to update all projects to the current version'.format(name_project))
        return False

    return True

def glob_create_batch(db_obj_project, request):
    name = request.POST['name']
    if name.strip() == '':
        name = uuid.uuid4().hex
        # name = token_urlsafe()

    return m_Batch.objects.create(
        name=name,
        fk_project=db_obj_project,
        title=request.POST['title'],
        description=request.POST['description'],
        keywords=request.POST['keywords'],
        count_assignments=request.POST['count_assignments'],
        use_sandbox=True if request.POST['use_sandbox'] == '1' else False,
        reward=request.POST['reward'],
        lifetime=request.POST['lifetime'],
        duration=request.POST['duration'],
        fk_template=m_Template.objects.get(fk_project=db_obj_project, id=request.POST['template']),
    )

def create_question(template, height_frame, dict_parameters):
    for key, value in dict_parameters.items():
        template = template.replace('${'+key+'}', value)

    return '''
        <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
            <HTMLContent><![CDATA['''+template+''']]></HTMLContent>
            <FrameHeight>'''+str(height_frame)+'''</FrameHeight>
        </HTMLQuestion>'''

def get_client(db_obj_project, use_sandbox=True):
    if use_sandbox:
        return boto3.client('mturk',
            aws_access_key_id=db_obj_project.fk_account_mturk.key_access,
            aws_secret_access_key=db_obj_project.fk_account_mturk.key_secret,
            region_name='us-east-1',
            endpoint_url=glob_url_sandbox
        )
    else:
        return boto3.client('mturk',
            aws_access_key_id=db_obj_project.fk_account_mturk.key_access,
            aws_secret_access_key=db_obj_project.fk_account_mturk.key_secret,
            region_name='us-east-1'
        )


glob_dict_properties_validate = {
    'string': lambda request, x: request.POST[x].strip() == '',
    'template': lambda request, x, y: request.POST[x].strip() == '' and not y in request.FILES,
    'number': lambda request, x: not request.POST[x].isdigit() or int(request.POST[x]) == 0,
}
def validate_form(request, list_inputs):
    is_valid = True

    dict_messages = {
        'error': [],
        'warning': [],
    }

    try:
        for item in list_inputs:
            if glob_dict_properties_validate[item['type']](request, *item['keys']):
                is_valid = False
                if 'state' in item:
                    dict_messages[item['state']].append(item['message'])
                else:
                    dict_messages['error'].append(item['message'])
    except KeyError:
        dict_messages['error'].append('Unexpected error, please cry')
        valid = False

    for message in dict_messages['error']:
        messages.error(request, message)
    for message in dict_messages['warning']:
        messages.warning(request, message)

    return is_valid

def get_code_js_md5():
    return '''var MD5=function(r){function n(o){if(t[o])return t[o].exports;var e=t[o]={i:o,l:!1,exports:{}};return r[o].call(e.exports,e,e.exports,n),e.l=!0,e.exports}var t={};return n.m=r,n.c=t,n.i=function(r){return r},n.d=function(r,t,o){n.o(r,t)||Object.defineProperty(r,t,{configurable:!1,enumerable:!0,get:o})},n.n=function(r){var t=r&&r.__esModule?function(){return r.default}:function(){return r};return n.d(t,"a",t),t},n.o=function(r,n){return Object.prototype.hasOwnProperty.call(r,n)},n.p="",n(n.s=4)}([function(r,n){var t={utf8:{stringToBytes:function(r){return t.bin.stringToBytes(unescape(encodeURIComponent(r)))},bytesToString:function(r){return decodeURIComponent(escape(t.bin.bytesToString(r)))}},bin:{stringToBytes:function(r){for(var n=[],t=0;t<r.length;t++)n.push(255&r.charCodeAt(t));return n},bytesToString:function(r){for(var n=[],t=0;t<r.length;t++)n.push(String.fromCharCode(r[t]));return n.join("")}}};r.exports=t},function(r,n,t){!function(){var n=t(2),o=t(0).utf8,e=t(3),u=t(0).bin,i=function(r,t){r.constructor==String?r=t&&"binary"===t.encoding?u.stringToBytes(r):o.stringToBytes(r):e(r)?r=Array.prototype.slice.call(r,0):Array.isArray(r)||(r=r.toString());for(var f=n.bytesToWords(r),s=8*r.length,c=1732584193,a=-271733879,l=-1732584194,g=271733878,h=0;h<f.length;h++)f[h]=16711935&(f[h]<<8|f[h]>>>24)|4278255360&(f[h]<<24|f[h]>>>8);f[s>>>5]|=128<<s%32,f[14+(s+64>>>9<<4)]=s;for(var p=i._ff,y=i._gg,v=i._hh,d=i._ii,h=0;h<f.length;h+=16){var b=c,T=a,x=l,B=g;c=p(c,a,l,g,f[h+0],7,-680876936),g=p(g,c,a,l,f[h+1],12,-389564586),l=p(l,g,c,a,f[h+2],17,606105819),a=p(a,l,g,c,f[h+3],22,-1044525330),c=p(c,a,l,g,f[h+4],7,-176418897),g=p(g,c,a,l,f[h+5],12,1200080426),l=p(l,g,c,a,f[h+6],17,-1473231341),a=p(a,l,g,c,f[h+7],22,-45705983),c=p(c,a,l,g,f[h+8],7,1770035416),g=p(g,c,a,l,f[h+9],12,-1958414417),l=p(l,g,c,a,f[h+10],17,-42063),a=p(a,l,g,c,f[h+11],22,-1990404162),c=p(c,a,l,g,f[h+12],7,1804603682),g=p(g,c,a,l,f[h+13],12,-40341101),l=p(l,g,c,a,f[h+14],17,-1502002290),a=p(a,l,g,c,f[h+15],22,1236535329),c=y(c,a,l,g,f[h+1],5,-165796510),g=y(g,c,a,l,f[h+6],9,-1069501632),l=y(l,g,c,a,f[h+11],14,643717713),a=y(a,l,g,c,f[h+0],20,-373897302),c=y(c,a,l,g,f[h+5],5,-701558691),g=y(g,c,a,l,f[h+10],9,38016083),l=y(l,g,c,a,f[h+15],14,-660478335),a=y(a,l,g,c,f[h+4],20,-405537848),c=y(c,a,l,g,f[h+9],5,568446438),g=y(g,c,a,l,f[h+14],9,-1019803690),l=y(l,g,c,a,f[h+3],14,-187363961),a=y(a,l,g,c,f[h+8],20,1163531501),c=y(c,a,l,g,f[h+13],5,-1444681467),g=y(g,c,a,l,f[h+2],9,-51403784),l=y(l,g,c,a,f[h+7],14,1735328473),a=y(a,l,g,c,f[h+12],20,-1926607734),c=v(c,a,l,g,f[h+5],4,-378558),g=v(g,c,a,l,f[h+8],11,-2022574463),l=v(l,g,c,a,f[h+11],16,1839030562),a=v(a,l,g,c,f[h+14],23,-35309556),c=v(c,a,l,g,f[h+1],4,-1530992060),g=v(g,c,a,l,f[h+4],11,1272893353),l=v(l,g,c,a,f[h+7],16,-155497632),a=v(a,l,g,c,f[h+10],23,-1094730640),c=v(c,a,l,g,f[h+13],4,681279174),g=v(g,c,a,l,f[h+0],11,-358537222),l=v(l,g,c,a,f[h+3],16,-722521979),a=v(a,l,g,c,f[h+6],23,76029189),c=v(c,a,l,g,f[h+9],4,-640364487),g=v(g,c,a,l,f[h+12],11,-421815835),l=v(l,g,c,a,f[h+15],16,530742520),a=v(a,l,g,c,f[h+2],23,-995338651),c=d(c,a,l,g,f[h+0],6,-198630844),g=d(g,c,a,l,f[h+7],10,1126891415),l=d(l,g,c,a,f[h+14],15,-1416354905),a=d(a,l,g,c,f[h+5],21,-57434055),c=d(c,a,l,g,f[h+12],6,1700485571),g=d(g,c,a,l,f[h+3],10,-1894986606),l=d(l,g,c,a,f[h+10],15,-1051523),a=d(a,l,g,c,f[h+1],21,-2054922799),c=d(c,a,l,g,f[h+8],6,1873313359),g=d(g,c,a,l,f[h+15],10,-30611744),l=d(l,g,c,a,f[h+6],15,-1560198380),a=d(a,l,g,c,f[h+13],21,1309151649),c=d(c,a,l,g,f[h+4],6,-145523070),g=d(g,c,a,l,f[h+11],10,-1120210379),l=d(l,g,c,a,f[h+2],15,718787259),a=d(a,l,g,c,f[h+9],21,-343485551),c=c+b>>>0,a=a+T>>>0,l=l+x>>>0,g=g+B>>>0}return n.endian([c,a,l,g])};i._ff=function(r,n,t,o,e,u,i){var f=r+(n&t|~n&o)+(e>>>0)+i;return(f<<u|f>>>32-u)+n},i._gg=function(r,n,t,o,e,u,i){var f=r+(n&o|t&~o)+(e>>>0)+i;return(f<<u|f>>>32-u)+n},i._hh=function(r,n,t,o,e,u,i){var f=r+(n^t^o)+(e>>>0)+i;return(f<<u|f>>>32-u)+n},i._ii=function(r,n,t,o,e,u,i){var f=r+(t^(n|~o))+(e>>>0)+i;return(f<<u|f>>>32-u)+n},i._blocksize=16,i._digestsize=16,r.exports=function(r,t){if(void 0===r||null===r)throw new Error("Illegal argument "+r);var o=n.wordsToBytes(i(r,t));return t&&t.asBytes?o:t&&t.asString?u.bytesToString(o):n.bytesToHex(o)}}()},function(r,n){!function(){var n="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",t={rotl:function(r,n){return r<<n|r>>>32-n},rotr:function(r,n){return r<<32-n|r>>>n},endian:function(r){if(r.constructor==Number)return 16711935&t.rotl(r,8)|4278255360&t.rotl(r,24);for(var n=0;n<r.length;n++)r[n]=t.endian(r[n]);return r},randomBytes:function(r){for(var n=[];r>0;r--)n.push(Math.floor(256*Math.random()));return n},bytesToWords:function(r){for(var n=[],t=0,o=0;t<r.length;t++,o+=8)n[o>>>5]|=r[t]<<24-o%32;return n},wordsToBytes:function(r){for(var n=[],t=0;t<32*r.length;t+=8)n.push(r[t>>>5]>>>24-t%32&255);return n},bytesToHex:function(r){for(var n=[],t=0;t<r.length;t++)n.push((r[t]>>>4).toString(16)),n.push((15&r[t]).toString(16));return n.join("")},hexToBytes:function(r){for(var n=[],t=0;t<r.length;t+=2)n.push(parseInt(r.substr(t,2),16));return n},bytesToBase64:function(r){for(var t=[],o=0;o<r.length;o+=3)for(var e=r[o]<<16|r[o+1]<<8|r[o+2],u=0;u<4;u++)8*o+6*u<=8*r.length?t.push(n.charAt(e>>>6*(3-u)&63)):t.push("=");return t.join("")},base64ToBytes:function(r){r=r.replace(/[^A-Z0-9+\/]/gi,"");for(var t=[],o=0,e=0;o<r.length;e=++o%4)0!=e&&t.push((n.indexOf(r.charAt(o-1))&Math.pow(2,-2*e+8)-1)<<2*e|n.indexOf(r.charAt(o))>>>6-2*e);return t}};r.exports=t}()},function(r,n){function t(r){return!!r.constructor&&"function"==typeof r.constructor.isBuffer&&r.constructor.isBuffer(r)}function o(r){return"function"==typeof r.readFloatLE&&"function"==typeof r.slice&&t(r.slice(0,0))}/*!
 * Determine if an object is a Buffer
 *
 * @author   Feross Aboukhadijeh <feross@feross.org> <http://feross.org>
 * @license  MIT
 */
r.exports=function(r){return null!=r&&(t(r)||o(r)||!!r._isBuffer)}},function(r,n,t){r.exports=t(1)}]);
    '''

def get_info_texts():
    link_documentation = reverse('mturk_manager:documentation')

    return {
        'batch_settings': (
            'Batch settings',
            '''
            <p>
                These settings will define your project wide batch properties.<br>
                Every time you create a new batch these settings are taken and used as properties for the new batch but you are able to override settings for the new batch.
            </p>
            '''
        ),
        'manage_template_worker': (
            'Worker templates',
            '''
            <p>
                A worker templates is mainly a HTML document which is used to define the layout of the task given to the worker.<br>
                Exactly one requester assignment and hit template can be connected to a worker template to define the layout of the results of the worker template.<br>
            </p>
            <p class="mb-0">Read more about worker templates in the <a href={}#link_templates_worker>Documentation</a>.</p>
            '''.format(link_documentation)
        ),
        'manage_template_requester_assignment': (
            'Requester assignment templates',
            '''
            <p>
                A requester assignment template defines the layout of the results of a assignment. <br>
            </p>
            <p class="mb-0">Read more about requester assignment templates in the <a href={}#link_templates_requester_assignemnt>Documentation</a>.</p>
            '''.format(link_documentation)
        ),
        'manage_template_requester_hit': (
            'Requester hit templates',
            '''
            <p>
                A requester hit template can be used to wrap the results of assignments sharing the same hit<br>
            </p>
            <p class="mb-0">Read more about hit assignment templates in the <a href={}#link_templates_requester_hit>Documentation</a>.</p>
            '''.format(link_documentation)
        ),
    }