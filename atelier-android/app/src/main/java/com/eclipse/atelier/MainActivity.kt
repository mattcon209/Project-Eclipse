package com.eclipse.atelier

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.util.concurrent.TimeUnit

private val Bg = Color(0xFF070708)
private val Copper = Color(0xFFC45C38)
private val Tungsten = Color(0xFFC4A574)
private val Mute = Color(0xFF8A847C)
private val Paper = Color(0xFFEDE8E1)
private val Line = Color(0xFF242428)
private val Surface = Color(0xFF121214)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val prefs = getSharedPreferences("atelier", MODE_PRIVATE)
        setContent {
            AtelierApp(
                initialToken = prefs.getString("token", "") ?: "",
                saveToken = { prefs.edit().putString("token", it).apply() },
            )
        }
    }
}

private val http = OkHttpClient.Builder()
    .connectTimeout(4, TimeUnit.SECONDS)
    .readTimeout(8, TimeUnit.SECONDS)
    .build()

@Composable
fun AtelierApp(initialToken: String, saveToken: (String) -> Unit) {
    var host by remember { mutableStateOf("http://10.0.2.2:7740") }
    var token by remember { mutableStateOf(initialToken) }
    var code by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Not paired.") }
    var err by remember { mutableStateOf("") }
    var paste by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()

    Column(
        Modifier
            .fillMaxSize()
            .background(Bg)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("ATELIER", color = Tungsten, fontSize = 13.sp, letterSpacing = 4.sp, fontFamily = FontFamily.Serif)
        Text("Phase 1 shell. Pair, then paste a model link.", color = Mute, fontSize = 14.sp)
        OutlinedTextField(
            value = host,
            onValueChange = { host = it },
            label = { Text("Engine URL") },
            modifier = Modifier.fillMaxWidth(),
            colors = fieldColors(),
        )
        if (token.isBlank()) {
            OutlinedTextField(
                value = code,
                onValueChange = { code = it.filter { ch -> ch.isDigit() }.take(6) },
                label = { Text("Pairing code") },
                modifier = Modifier.fillMaxWidth(),
                colors = fieldColors(),
            )
            Button(
                onClick = {
                    err = ""
                    scope.launch {
                        runCatching { pair(host, code) }
                            .onSuccess {
                                token = it
                                saveToken(it)
                                status = "Paired."
                            }
                            .onFailure { err = it.message ?: "Pair failed" }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = Copper, contentColor = Color(0xFF1A0C08)),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth(),
            ) { Text("PAIR THIS PHONE", letterSpacing = 2.sp) }
        }
        Row(
            Modifier
                .border(1.dp, Line, RoundedCornerShape(12.dp))
                .background(Surface, RoundedCornerShape(12.dp))
                .padding(14.dp)
                .fillMaxWidth(),
        ) {
            Text(status, color = Paper, fontSize = 14.sp)
        }
        Button(
            onClick = {
                err = ""
                scope.launch {
                    runCatching { fetchStatus(host, token) }
                        .onSuccess { status = it }
                        .onFailure { err = it.message ?: "Unreachable" }
                }
            },
            colors = ButtonDefaults.buttonColors(containerColor = Copper, contentColor = Color(0xFF1A0C08)),
            shape = RoundedCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth(),
        ) { Text("PING ENGINE", letterSpacing = 2.sp) }
        if (token.isNotBlank()) {
            OutlinedTextField(
                value = paste,
                onValueChange = { paste = it },
                label = { Text("Paste model link") },
                modifier = Modifier.fillMaxWidth(),
                colors = fieldColors(),
            )
            Button(
                onClick = {
                    err = ""
                    scope.launch {
                        runCatching { acquire(host, token, paste) }
                            .onSuccess { status = it }
                            .onFailure { err = it.message ?: "Acquire failed" }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = Copper, contentColor = Color(0xFF1A0C08)),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth(),
            ) { Text("ADD TO LIBRARY", letterSpacing = 2.sp) }
            Button(
                onClick = {
                    err = ""
                    scope.launch {
                        runCatching { searchPc(host, token) }
                            .onSuccess { status = it }
                            .onFailure { err = it.message ?: "Search failed" }
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = Surface, contentColor = Paper),
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier.fillMaxWidth(),
            ) { Text("SEARCH THIS PC", letterSpacing = 2.sp) }
        }
        if (err.isNotBlank()) Text(err, color = Copper, fontSize = 13.sp)
        Text("Lab UI (same protocol) is served by the engine at /", color = Mute, fontSize = 12.sp)
    }
}

@Composable
private fun fieldColors() = TextFieldDefaults.colors(
    focusedTextColor = Paper,
    unfocusedTextColor = Paper,
    focusedContainerColor = Surface,
    unfocusedContainerColor = Surface,
    focusedLabelColor = Mute,
    unfocusedLabelColor = Mute,
    cursorColor = Copper,
    focusedIndicatorColor = Copper,
    unfocusedIndicatorColor = Line,
)

private suspend fun pair(host: String, code: String): String = withContext(Dispatchers.IO) {
    val body = JSONObject().put("code", code).put("device_name", "Galaxy S24+").toString()
    val req = Request.Builder()
        .url(host.trimEnd('/') + "/api/pair")
        .post(body.toRequestBody("application/json".toMediaType()))
        .build()
    http.newCall(req).execute().use { res ->
        val json = JSONObject(res.body?.string() ?: "{}")
        if (!res.isSuccessful) error(json.optString("error", "Pair failed"))
        json.getString("token")
    }
}

private suspend fun acquire(host: String, token: String, url: String): String = withContext(Dispatchers.IO) {
    val longHttp = http.newBuilder().readTimeout(120, TimeUnit.SECONDS).build()
    val body = JSONObject().put("url", url).put("confirm", true).toString()
    val req = Request.Builder()
        .url(host.trimEnd('/') + "/api/library/acquire")
        .header("Authorization", "Bearer $token")
        .post(body.toRequestBody("application/json".toMediaType()))
        .build()
    longHttp.newCall(req).execute().use { res ->
        val json = JSONObject(res.body?.string() ?: "{}")
        if (res.code == 409) error(json.optString("reason", "Won’t fit"))
        if (!res.isSuccessful) error(json.optString("detail", json.optString("error", "Acquire failed")))
        val rec = json.optJSONObject("record")
        val state = rec?.optString("state") ?: "ok"
        val name = rec?.optString("name") ?: url
        "$state · $name"
    }
}

private suspend fun searchPc(host: String, token: String): String = withContext(Dispatchers.IO) {
    val longHttp = http.newBuilder().readTimeout(120, TimeUnit.SECONDS).build()
    val req = Request.Builder()
        .url(host.trimEnd('/') + "/api/library/search")
        .header("Authorization", "Bearer $token")
        .post("{}".toRequestBody("application/json".toMediaType()))
        .build()
    longHttp.newCall(req).execute().use { res ->
        val json = JSONObject(res.body?.string() ?: "{}")
        if (!res.isSuccessful) error(json.optString("detail", json.optString("error", "Search failed")))
        val found = json.optInt("found")
        val added = json.optInt("added")
        val ready = json.optInt("ready")
        "Found $found · added $added · $ready Ready"
    }
}

private suspend fun fetchStatus(host: String, token: String): String = withContext(Dispatchers.IO) {
    val b = Request.Builder().url(host.trimEnd('/') + "/api/status")
    if (token.isNotBlank()) b.header("Authorization", "Bearer $token")
    http.newCall(b.build()).execute().use { res ->
        val json = JSONObject(res.body?.string() ?: "{}")
        val gpu = json.optJSONObject("resources")?.optJSONObject("gpu")
        val hostName = json.optJSONObject("resources")?.optString("hostname") ?: "?"
        val vram = gpu?.opt("vram_used_mb")
        "engine ${json.optString("engine")} · $hostName · vram $vram · paired ${json.optBoolean("paired")}"
    }
}
