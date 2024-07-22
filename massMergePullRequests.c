#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>

#define TOKEN "your-token"

struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if(ptr == NULL) {
        printf("Not enough memory (realloc returned NULL)\n");
        return 0;
    }

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

void get_all_pages(const char *url, struct MemoryStruct *chunk) {
    CURL *curl_handle;
    CURLcode res;

    curl_global_init(CURL_GLOBAL_ALL);
    curl_handle = curl_easy_init();

    if(curl_handle) {
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Authorization: token " TOKEN);

        curl_easy_setopt(curl_handle, CURLOPT_URL, url);
        curl_easy_setopt(curl_handle, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
        curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)chunk);

        res = curl_easy_perform(curl_handle);

        if(res != CURLE_OK) {
            fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
        }

        curl_easy_cleanup(curl_handle);
        curl_slist_free_all(headers);
    }

    curl_global_cleanup();
}

int main(void) {
    struct MemoryStruct chunk;
    chunk.memory = malloc(1);
    chunk.size = 0;

    get_all_pages("https://api.github.com/user/repos", &chunk);

    if(chunk.memory) {
        printf("%s\n", chunk.memory);
        free(chunk.memory);
    }

    return 0;
}
