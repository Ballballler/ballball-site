
/* Shared deterministic preview rendering. Three.js is bundled locally. */
(()=>{'use strict';
const VERSION='1.1.0',SKILLS={website:'website-design',art:'creative-generative-art',hardware:'creative-hardware-mg'},PARAM_KEYS=['title','subtitle','accent','intensity','seed'],OUTPUT_KEYS=['kind','width','height','fps','duration'],INPUT_KEYS=['dragX','dragY','progress'],LOCALES=['en_US','fr_FR','ja_JP','ko_KR','zh_CN','zh_CN_CUSTOM'],HASH=/^[a-f0-9]{64}$/,cache=new Map();let renderer=null,failed=false;
const items=()=>[...(window.CreativeWebsiteDesign||[]),...(window.CreativeArt||[]),...(window.CreativeHardware||[])];
const input=()=>({x:0,y:0,dragX:0,dragY:0,progress:0.42,active:false});
const message=key=>window.CreativeI18n?.errors?.[key]||key;
const wellFormed=value=>!Array.from(value).some(c=>c.length===1&&c.charCodeAt(0)>=0xd800&&c.charCodeAt(0)<=0xdfff);
function initialState(value){const state=input();if(value===undefined)return state;if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).length!==3||Object.keys(value).some(key=>!INPUT_KEYS.includes(key)))throw Error(message('initialStateShape'));for(const [key,min,max]of [['dragX',-2,2],['dragY',-1,1],['progress',0,1]]){if(typeof value[key]!=='number'||!Number.isFinite(value[key])||value[key]<min||value[key]>max)throw Error(message('initialStateRange'));state[key]=value[key]}return state}
function savedInput(value){return Object.fromEntries(INPUT_KEYS.map(key=>[key,value[key]]))}
function dispose(entry){if(!entry)return;entry.dispose?.();const seen=new Set();function release(v){if(v&&typeof v.dispose==='function'&&!seen.has(v)){seen.add(v);v.dispose()}}entry.scene?.traverse(object=>{if(object.isInstancedMesh)release(object);if(object.isLight)release(object.shadow);release(object.geometry);for(const material of (Array.isArray(object.material)?object.material:[object.material])){if(!material)continue;for(const v of Object.values(material))if(v?.isTexture)release(v);release(material)}});release(entry.scene?.environment);if(entry.scene?.background?.isTexture)release(entry.scene.background)}
function clear(){for(const entry of cache.values())dispose(entry);cache.clear();renderer?.renderLists.dispose()}
function getRenderer(){if(failed)throw Error(message('webglUnsupported'));if(!renderer){try{renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true,powerPreference:'low-power'});renderer.setPixelRatio(1);renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap}catch(e){failed=true;throw e}}return renderer}
function scene(item){if(cache.has(item.id)){const v=cache.get(item.id);cache.delete(item.id);cache.set(item.id,v);return v}const value=item.create(THREE);if(!value?.scene||!value?.camera||typeof value.update!=='function')throw Error(message('invalidScene'));cache.set(item.id,value);while(cache.size>12){const key=cache.keys().next().value;dispose(cache.get(key));cache.delete(key)}return value}
function render(item,canvas,t,params,interaction=input()){
 const c=canvas.getContext('2d');if(!c)throw Error(message('canvasUnavailable'));c.save();
 try{c.setTransform(1,0,0,1,0,0);c.globalAlpha=1;c.globalCompositeOperation='source-over';c.clearRect(0,0,canvas.width,canvas.height);
  if(item.create){const r=getRenderer();if(r.getContext().isContextLost())throw Error(message('contextUnavailable'));const entry=scene(item);if(r.domElement.width!==canvas.width||r.domElement.height!==canvas.height)r.setSize(canvas.width,canvas.height,false);entry.update(t,params,interaction);if(entry.camera.isPerspectiveCamera){entry.camera.aspect=canvas.width/canvas.height;entry.camera.updateProjectionMatrix()}r.render(entry.scene,entry.camera);c.drawImage(r.domElement,0,0);c.setTransform(canvas.width/1200,0,0,canvas.height/675,0,0);item.overlay?.(c,t,params,interaction)}
  else{c.setTransform(canvas.width/1200,0,0,canvas.height/675,0,0);c.fillStyle=item.bg||'#f4f3ee';c.fillRect(0,0,1200,675);item.draw(c,t,params,interaction)}
 }finally{c.restore()}
}
function validate(value){
 if(!value||typeof value!=='object'||Array.isArray(value)||value.schema_version!==1||value.library_version!==VERSION)throw Error(message('unsupportedSpec'));
 if(typeof value.catalog_sha256!=='string'||!HASH.test(value.catalog_sha256))throw Error(message('catalogInvalid'));
 if(!LOCALES.includes(value.locale))throw Error(message('localeInvalid'));
 if(Object.hasOwn(value,'initial_state')){initialState(value.initial_state);if(value.initial_state===undefined)throw Error(message('emptyInitialState'))}
 const item=items().find(x=>x.id===value.template_id&&x.family===value.family);if(!item)throw Error(message('templateFamily'));
 if(value.skill!==SKILLS[item.family])throw Error(message('skillFamily'));
 const p=value.parameters;if(!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).length!==PARAM_KEYS.length||Object.keys(p).some(k=>!PARAM_KEYS.includes(k)))throw Error(message('parameters'));
 for(const [key,max]of [['title',40],['subtitle',100]])if(typeof p[key]!=='string'||Array.from(p[key]).length>max||!wellFormed(p[key])||(key==='title'&&!p[key].trim()))throw Error(message(key==='title'?'titleInvalid':'subtitleInvalid'));
 if(typeof p.accent!=='string'||!/^#[0-9a-fA-F]{6}$/.test(p.accent))throw Error(message('accentInvalid'));
 if(typeof p.intensity!=='number'||!Number.isFinite(p.intensity)||p.intensity<0||p.intensity>1)throw Error(message('intensityInvalid'));
 if(!Number.isInteger(p.seed)||p.seed<0||p.seed>99999)throw Error(message('seedInvalid'));
 const o=value.output;if(!o||typeof o!=='object'||Array.isArray(o)||Object.keys(o).length!==OUTPUT_KEYS.length||Object.keys(o).some(k=>!OUTPUT_KEYS.includes(k))||o.kind!==(item.family==='website'?'interactive-html':'animation-html')||!Number.isInteger(o.width)||!Number.isInteger(o.height)||o.width*9!==o.height*16||o.width<320||o.width>3840||o.height<180||o.height>2160||![24,25,30,60].includes(o.fps)||o.duration!==item.duration)throw Error(message('outputInvalid'));
 if(value.user_request!==undefined&&(typeof value.user_request!=='string'||Array.from(value.user_request).length>2000||!wellFormed(value.user_request)))throw Error(message('requestInvalid'));return {item,spec:JSON.parse(JSON.stringify(value))};
}
function spec(item,params,request='',initial,locale=window.CreativeLocale||'zh_CN',catalogSha256=window.CreativeCatalogSha256){if(!params||typeof params!=='object'||Array.isArray(params)||Object.keys(params).some(k=>!PARAM_KEYS.includes(k)))throw Error(message('parameters'));const parameters=Object.fromEntries(PARAM_KEYS.map(key=>[key,params[key]]));const result={schema_version:1,library_version:VERSION,catalog_sha256:catalogSha256,locale,skill:SKILLS[item.family],family:item.family,template_id:item.id,template_name:item.name,parameters,output:{kind:item.family==='website'?'interactive-html':'animation-html',width:1200,height:675,fps:60,duration:item.duration},user_request:request};if(initial!==undefined)result.initial_state=savedInput(initialState(initial));return result}
window.CreativeRuntime={version:VERSION,items,input,initialState,savedInput,render,clear,validate,spec};
window.addEventListener('pagehide',()=>{clear();renderer?.dispose();renderer=null});
})();

