const TOKEN_KEY="token"
const INFO = "health-info";
const ACTIVE_PATH="active_key"
export function getToken(){
    return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token){
    sessionStorage.setItem(TOKEN_KEY,token);
}

export function isCurrentToken(expectedToken){
    return getToken() === expectedToken;
}

export function getHealthInfo(){
    const raw = sessionStorage.getItem(INFO);
    if (raw) {
        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }
    return null;
}

export function setHealthInfo(obj){
    sessionStorage.setItem(INFO, JSON.stringify(obj));
}

export function clearToken(){
    sessionStorage.clear();
}

export function clearTokenIfCurrent(expectedToken){
    if (!isCurrentToken(expectedToken)) return false;
    clearToken();
    return true;
}
export function getActivePath(){
    return sessionStorage.getItem(ACTIVE_PATH);
}

export function setActivePath(path){
    sessionStorage.setItem(ACTIVE_PATH, path);
}
